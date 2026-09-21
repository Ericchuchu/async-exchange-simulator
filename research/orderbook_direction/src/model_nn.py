import torch
import torch.nn as nn

class NeuralNetwork(nn.Module):
    def __init__(self, input_size, num_classes, hidden_sizes=[64, 128]):
        super(NeuralNetwork, self).__init__()
        self.hidden_layers = nn.ModuleList()
        
        self.hidden_layers.append(nn.Linear(input_size, hidden_sizes[0]))
        self.hidden_layers.append(nn.Dropout(p=0.1))
        for i in range(1, len(hidden_sizes)):
            if i == (len(hidden_sizes)-1):
                self.hidden_layers.append(nn.Linear(hidden_sizes[i-1], hidden_sizes[i]))
            else:
                self.hidden_layers.append(nn.Linear(hidden_sizes[i-1], hidden_sizes[i]))
                self.hidden_layers.append(nn.Dropout(p=0.1))

        self.output = nn.Linear(hidden_sizes[-1], num_classes)
    
    def forward(self, x):
        
        for layer in self.hidden_layers:
            x = layer(x)
            if isinstance(layer, nn.Linear):
                x = torch.relu(x)
        
        x = self.output(x)
        x = torch.softmax(x, dim=1)   
        return x 
    
if __name__ == '__main__':
    input = torch.zeros((1,8))
    factor = torch.zeros((1,1))
    input_size = 8
    hidden_size = [16,64,64]
    num_class = 3
    model = NeuralNetwork(input_size,num_class, hidden_size)
    print(model(input, factor).shape)