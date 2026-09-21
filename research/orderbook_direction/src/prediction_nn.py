import argparse
import torch
import random
import numpy as np
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from torch.optim.lr_scheduler import StepLR
from model_nn import NeuralNetwork
from train_test_valid import train, test, validate
from data_preprocess import preprocess
from loss_function import adjusted_loss_fn

def set_seed(seed_value=0):
    torch.manual_seed(seed_value)
    torch.cuda.manual_seed_all(seed_value) 
    np.random.seed(seed_value)
    random.seed(seed_value)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

if __name__ == '__main__':
    set_seed()  
    parser = argparse.ArgumentParser(description='Neural Network Training')
    parser.add_argument('--symbol', type=str, default="SPOT_BTC_USDT", help='symbol of the data')
    parser.add_argument('--batch-size', type=int, default=32, help='input batch size for training (default: 32)')
    parser.add_argument('--num-epochs', type=int, default=500, help='number of epochs to train (default: 10)')
    parser.add_argument('--input-size', type=int, default=6, help='input size of the model')
    parser.add_argument('--output-size', type=int, default=3, help='output size of the model')
    parser.add_argument('--l1-weight', type=float, default=1e-6, help='weight of L1 regularization')
    parser.add_argument('--l2-weight', type=float, default=1e-6, help='weight of L2 regularization')
    parser.add_argument('--lr', type=float, default=1e-6, help='learning rate (default: 0.001)')
    parser.add_argument('--normalize', type=bool, default=True, help='normalize the data')

    args = parser.parse_args()

    train_data, train_labels, factor = preprocess(args.symbol, 'train')
    test_data, test_labels, factor = preprocess(args.symbol, 'test')
    valid_data, valid_labels, factor = preprocess(args.symbol, 'valid')

    train_data = torch.tensor(train_data, dtype=torch.float32)
    train_labels = torch.tensor(train_labels, dtype=torch.long)
    test_data = torch.tensor(test_data, dtype=torch.float32)
    test_labels = torch.tensor(test_labels, dtype=torch.long)
    valid_data = torch.tensor(valid_data, dtype=torch.float32)
    valid_labels = torch.tensor(valid_labels, dtype=torch.long)

    if args.normalize:
        train_mean = torch.mean(train_data, dim=0)
        train_std = torch.std(train_data, dim=0)
        eplison = 1e-9

        train_data = (train_data - train_mean) / (train_std + eplison)
        valid_data = (valid_data - train_mean) / (train_std + eplison)
        test_data = (test_data - train_mean) / (train_std + eplison)

    train_dataset = TensorDataset(train_data,train_labels)
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)

    valid_dataset = TensorDataset(valid_data,valid_labels)
    valid_loader = DataLoader(valid_dataset, batch_size=args.batch_size)

    test_dataset = TensorDataset(test_data,test_labels)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size)

    model = NeuralNetwork(args.input_size, args.output_size)

    criterion = adjusted_loss_fn(weight=0.3, l1_weight=args.l1_weight, l2_weight=args.l2_weight)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = StepLR(optimizer, step_size=30, gamma=0.1)

    for epoch in range(args.num_epochs):
        train_loss, train_accuracy = train(model, train_loader, criterion, optimizer)
        valid_loss, valid_accuracy, valid_precision, valid_f1, valid_recall = validate(model, valid_loader, criterion)
        
        print(f'Epoch [{epoch+1}/{args.num_epochs}], Train Loss: {train_loss:.4f}, Train Accuracy: {train_accuracy:.4f}, Valid Loss: {valid_loss:.4f}, ',
            f'Valid Accuracy: {valid_accuracy:.4f}, Valid Precision: {valid_precision:.4f}, ',
            f'Valid F1 Score: {valid_f1:.4f}, Valid Recall: {valid_recall:.4f}')

    test_accuracy, test_precision, test_f1, test_recall = test(model, test_loader)
    print(f'Test Accuracy: {test_accuracy:.4f}, Test Precision: {test_precision:.4f}, ',
        f'Test F1 Score: {test_f1:.4f}, Test Recall: {test_recall:.4f}')