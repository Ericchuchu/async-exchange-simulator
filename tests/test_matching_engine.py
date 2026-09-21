"""Offline tests for the matching engine: synthetic order-book snapshots, no network."""
import asyncio
import os
import tempfile
import unittest

from simulator.matching_engine import MatchingEngine

SYMBOL = "PERP_BTC_USDT"


def snapshot(ts, bids, asks):
    """WOO X order-book message: bids are sorted best (highest) first, asks best (lowest) first."""
    return {"topic": f"{SYMBOL}@orderbook", "ts": ts, "data": {"bids": bids, "asks": asks}}


class MatchingEngineTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)  # the engine writes trade_data/ and position_data/ here
        self.engine = MatchingEngine(server=None)
        await self.engine.handle_market_data(
            snapshot(1, bids=[[100.0, 1.0], [99.0, 2.0], [98.0, 3.0]], asks=[[101.0, 1.0], [102.0, 2.0]]))

    async def asyncTearDown(self):
        await self.engine.handle_cancel_all_pending_orders()
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
        os.chdir(self._cwd)
        self._tmp.cleanup()

    async def send(self, side, price, quantity, client_order_id, order_type="LIMIT"):
        confirmation = await self.engine.handle_order({
            "symbol": SYMBOL, "client_order_id": client_order_id, "order_type": order_type,
            "order_price": price, "order_quantity": quantity, "side": side})
        self.assertTrue(confirmation["success"])
        await asyncio.sleep(0.3)  # let the matching coroutine see the snapshot

    def fills(self, client_order_id):
        return [r for r in self.engine.trade_reports
                if r["clientOrderId"] == client_order_id and r["executedQuantity"] > 0]

    async def test_marketable_sell_fills_at_best_bid(self):
        await self.send("SELL", 99.5, 0.5, client_order_id=1)
        fills = self.fills(1)
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0]["executedPrice"], 100.0)
        self.assertEqual(fills[0]["executedQuantity"], 0.5)
        self.assertFalse(fills[0]["maker"])
        self.assertAlmostEqual(fills[0]["fee"], 0.0005 * 100.0 * 0.5)  # perpetual taker fee
        self.assertEqual(self.engine.position["LONG"][SYMBOL], -0.5)

    async def test_sell_walks_down_the_bids(self):
        await self.send("SELL", 99.0, 2.0, client_order_id=2)
        fills = self.fills(2)
        self.assertEqual(sum(f["executedQuantity"] for f in fills), 2.0)
        self.assertAlmostEqual(fills[0]["executedPrice"], (100.0 * 1.0 + 99.0 * 1.0) / 2.0)

    async def test_marketable_buy_fills_at_best_ask_and_rests_remainder(self):
        await self.send("BUY", 101.5, 1.5, client_order_id=3)
        fills = self.fills(3)
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0]["executedPrice"], 101.0)
        self.assertEqual(fills[0]["executedQuantity"], 1.0)
        self.assertIn(3, self.engine.client_orders)  # 0.5 is still resting

    async def test_ioc_sell_takes_the_best_bids_first(self):
        await self.send("SELL", 99.0, 2.0, client_order_id=5, order_type="IOC")
        fills = self.fills(5)
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0]["executedQuantity"], 2.0)
        # 1.0 @ 100 + 1.0 @ 99 = 199 (taking the worst bids first would give 198); IOC reports
        # carry the limit price as executedPrice, so the traded amount is checked through the fee
        self.assertAlmostEqual(fills[0]["fee"], 0.0005 * 199.0)

    async def test_resting_sell_fills_as_maker_when_the_bid_reaches_it(self):
        # Pins the simulator's rule, not exchange behaviour: a resting order is filled at the
        # book price (106) rather than at its own limit (105), and pays the maker fee.
        await self.send("SELL", 105.0, 1.0, client_order_id=4)
        self.assertEqual(self.fills(4), [])
        await self.engine.handle_market_data(snapshot(2, bids=[[106.0, 5.0], [105.0, 1.0]], asks=[[107.0, 1.0]]))
        await asyncio.sleep(0.3)
        fills = self.fills(4)
        self.assertEqual(len(fills), 1)
        self.assertEqual(fills[0]["executedPrice"], 106.0)
        self.assertTrue(fills[0]["maker"])
        self.assertAlmostEqual(fills[0]["fee"], 0.0002 * 106.0 * 1.0)  # perpetual maker fee


if __name__ == "__main__":
    unittest.main()
