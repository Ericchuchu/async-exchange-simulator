import torch
from torch import nn

def multi_class_precision_loss(outputs, targets, num_classes = 3, smooth=1e-6):
    probabilities = torch.softmax(outputs, dim=1)
    targets_one_hot = torch.nn.functional.one_hot(targets, num_classes=num_classes)
    
    precisions = []
    for c in range(num_classes):
        class_probabilities = probabilities[:, c]
        class_targets = targets_one_hot[:, c]
        true_positives = torch.sum(class_probabilities * class_targets)
        predicted_positives = torch.sum(class_probabilities)
        precision = true_positives / (predicted_positives + smooth)
        precisions.append(precision)
 
    average_precision = torch.mean(torch.stack(precisions))
    return 1 - average_precision

class weighted_cross_entropy_loss(nn.Module):
    def __init__(self):
        super(weighted_cross_entropy_loss, self).__init__()
        self.weights = torch.tensor([3.8,3.8, 1])  
        self.ce_loss = nn.CrossEntropyLoss(weight=self.weights)

    def forward(self, outputs, targets):
        return self.ce_loss(outputs, targets)
    
class adjusted_loss_fn(nn.Module):
    def __init__(self, weight=0.5, l1_weight=0.01, l2_weight=0.01):
        super(adjusted_loss_fn, self).__init__()
        self.weight = weight
        self.l1_weight = l1_weight
        self.l2_weight = l2_weight
        self.weighted_ce = weighted_cross_entropy_loss()
        self.pr_loss = multi_class_precision_loss
    
    def forward(self, outputs, targets, model):
        ce_loss = self.weighted_ce(outputs, targets)
        pr_loss = self.pr_loss(outputs, targets)
        combined_loss = (self.weight * pr_loss) + ((1 - self.weight) * ce_loss)
        
        # L1 regularization
        l1_reg = torch.tensor(0., requires_grad=True)
        for name, param in model.named_parameters():
            if 'weight' in name:
                l1_reg = l1_reg + torch.norm(param, 1)
        
        # L2 regularization
        l2_reg = torch.tensor(0., requires_grad=True)
        for name, param in model.named_parameters():
            if 'weight' in name:
                l2_reg = l2_reg + torch.norm(param, 2)
        
        final_loss = combined_loss + self.l1_weight * l1_reg + self.l2_weight * l2_reg
        return final_loss