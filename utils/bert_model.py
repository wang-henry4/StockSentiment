import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from torchvision.transforms import Compose
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

class twitData(Dataset):
    def __init__(self, json_path, transform=None):
        with open(json_path, "r") as file:
            self.data = list(file.readlines())
        self.transform = transform
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        example = json.loads(self.data[idx])
        sample = {"text": example["body"], "label": example["label"]}
        
        if self.transform:
            sample = self.transform(sample)
        return sample

class tokenize:
    def __init__(self, tokenizer, max_length):
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __call__(self, sample):
        text, label = sample["text"], sample["label"]
        text = self.tokenizer.encode(text, 
                                 max_length=self.max_length,
                                 pad_to_max_length=True)
        if label == "Bullish":
            label = 1
        else:
            label = 0
        return {"text": text, "label": label}
    
class toTensor:
    def __call__(self, sample):
        text = sample["text"]
        label = sample["label"]
        
        
        return {"text": torch.tensor(text),
                "label": torch.tensor(label)}

def get_dataset(json_path, max_length=128, token_vocab="bert-base-uncased"):
    """
    sets up the dataset object with tokenizer
    """
    tokenizer = BertTokenizer.from_pretrained(token_vocab)
    data = twitData(json_path, transform=Compose([tokenize(tokenizer, max_length), toTensor()]))
    return data