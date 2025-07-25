# 用Bert完成ner 
# 改造模型，使用BERT来完成NER任务。以下是改造后的model.py文件，其他文件保持不变
# -*- coding: utf-8 -*-

import torch
import torch.nn as nn
from torch.optim import Adam, SGD
from torchcrf import CRF
from transformers import BertModel, BertConfig

"""
建立网络模型结构
"""


class TorchModel(nn.Module):
    def __init__(self, config):
        super(TorchModel, self).__init__()
        self.bert_config = BertConfig.from_pretrained(config["bert_path"])
        self.bert = BertModel.from_pretrained(config["bert_path"])

        hidden_size = self.bert_config.hidden_size
        class_num = config["class_num"]

        # 冻结BERT参数
        for param in self.bert.parameters():
            param.requires_grad = False

        self.classify = nn.Linear(hidden_size, class_num)
        self.crf_layer = CRF(class_num, batch_first=True)
        self.use_crf = config["use_crf"]
        self.loss = torch.nn.CrossEntropyLoss(ignore_index=-1)  # loss采用交叉熵损失

    # 当输入真实标签，返回loss值；无真实标签，返回预测值
    def forward(self, x, target=None):
        # 获取BERT输出
        bert_output = self.bert(x)
        x = bert_output.last_hidden_state  # shape: (batch_size, seq_len, hidden_size)

        predict = self.classify(x)  # output: (batch_size, seq_len, num_tags)

        if target is not None:
            if self.use_crf:
                mask = target.gt(-1)
                return - self.crf_layer(predict, target, mask, reduction="mean")
            else:
                # (number, class_num), (number)
                return self.loss(predict.view(-1, predict.shape[-1]), target.view(-1))
        else:
            if self.use_crf:
                return self.crf_layer.decode(predict)
            else:
                return predict


def choose_optimizer(config, model):
    optimizer = config["optimizer"]
    learning_rate = config["learning_rate"]
    if optimizer == "adam":
        return Adam(model.parameters(), lr=learning_rate)
    elif optimizer == "sgd":
        return SGD(model.parameters(), lr=learning_rate)


if __name__ == "__main__":
    from config import Config

    model = TorchModel(Config)
