import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import BertModel, BertTokenizer

def clsPoolFunc(hiddenStates):
    return hiddenStates[:,0]

def avgPoolFunc(hiddenStates):
    return torch.mean(hiddenStates, dim=1)

class Pooler(nn.Module):
    def __init__(self, hiddenSize, poolFunc):
        super().__init__()
        self.poolFunc = poolFunc
        self.dense = nn.Linear(hiddenSize, hiddenSize)
        self.activation = nn.Tanh()
    
    def forward(self, hiddenStates):
        firstToken = self.poolFunc(hiddenStates)
        pooled_out = self.dense(firstToken)
        pooled_out = self.activation(pooled_out)
        return pooled_out
    
class BertFineTuned(nn.Module):
    def __init__(self, out_dim, poolFunc, hiddenStates=768):
        """
        out_dim is the dim of the output, default is 2 for sentiment classification
        poolFunc is the function for pooling the output embedings of bert, 
            suggested to use avgPoolFunc
        hiddenStates is the dim of output embeddings of bert, default is 768
        """
        super().__init__()
        self.bert = BertModel.from_pretrained("bert-base-uncased")
        self.pooler = Pooler(hiddenStates, poolFunc)
        self.dense = nn.Linear(hiddenStates, out_dim)
        self.trainable = [*self.pooler.parameters(), *self.dense.parameters()]

    def forward(self, x):
        x = self.bert(x)
        x = self.pooler(x[0])
        x = self.dense(x)
        x = F.softmax(x, dim=1)
        return x