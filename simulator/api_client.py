import aiohttp
import asyncio
import json

class ExchangeSimulatorAPIClient:
    def __init__(self, base_url='ws://localhost:8765/api'):
        self.base_url = base_url

    async def make_request(self, session, method, params=None):
        async with session.ws_connect(self.base_url) as websocket:
            request = {"method": method, "params": params}
            await websocket.send_json(request)
            response = await websocket.receive_json()
            return response

    async def send_order(self, session, params):
        return await self.make_request(session, "send_order", params)

    async def send_algo_order(self, session, params):
        return await self.make_request(session, "send_algo_order", params)

    async def edit_order_by_client_order_id(self, session, params):
        return await self.make_request(session, "edit_order_by_client_order_id", params)

    async def cancel_order_by_client_order_id(self, session, params):
        return await self.make_request(session, "cancel_order_by_client_order_id", params)

    async def cancel_order(self, session, params):
        return await self.make_request(session, "cancel_order", params)

    async def cancel_orders(self, session, params):
        return await self.make_request(session, "cancel_orders", params)

    async def cancel_all_pending_orders(self, session, params=None):
        return await self.make_request(session, "cancel_all_pending_orders", params)

    async def get_open_orders(self, session, params=None):
        return await self.make_request(session, "get_open_orders", params)

    async def get_order_info(self, session, params):
        return await self.make_request(session, "get_order_info", params)

    async def get_positions(self, session, params=None):
        return await self.make_request(session, "get_positions", params)

    async def get_account_info(self, session, params=None):
        return await self.make_request(session, "get_account_info", params)

    async def get_balance(self, session, params=None):
        return await self.make_request(session, "get_balance", params)

    async def transfer(self, session, params):
        return await self.make_request(session, "transfer", params)


# example
# async def main():
#     client = ExchangeSimulatorAPIClient()

#     async with aiohttp.ClientSession() as session:
#         try:
#             order_params = {
#                 "symbol": "PERP_BTC_USDT",
#                 "side": "BUY",
#                 "order_type": "LIMIT",
#                 "order_price": 30000,
#                 "order_quantity": 0.01,
#                 "position_side":"LONG"
#             }
#             response = await client.send_order(session, order_params)
#             print("Order Response:", response)

#             balance_response = await client.get_balance(session)
#             print("Balance Response:", balance_response)

#         except Exception as e:
#             print(f"Error: {e}")

# asyncio.run(main())