import numpy as np
import torch
from torch import nn


class GRN(nn.Module):
    def __init__(self, width):
        super().__init__()
        self.hidden = nn.Sequential(nn.Linear(width, width), nn.ELU(), nn.Linear(width, 2 * width))
        self.norm = nn.LayerNorm(width)

    def forward(self, x):
        return self.norm(x + nn.functional.glu(self.hidden(x), dim=-1))


class Fusion(nn.Module):
    """TFT compacto con selección variable, contexto, recurrencia y atención causal."""
    def __init__(self, features, groups, width=24):
        super().__init__()
        self.static = nn.Embedding(groups, width)
        self.horizon = nn.Embedding(5, width)
        self.variables = nn.ModuleList(nn.Sequential(nn.Linear(1, width), GRN(width)) for _ in range(features))
        self.selection = nn.Sequential(nn.Linear(features + width, width), GRN(width), nn.Linear(width, features))
        self.context = GRN(width)
        self.encoder = nn.LSTM(width, width, batch_first=True)
        self.decoder = nn.LSTM(width, width, batch_first=True)
        self.enrich = GRN(width)
        self.attention = nn.MultiheadAttention(width, 2, batch_first=True)
        self.output = nn.Sequential(GRN(width), nn.Linear(width, 3))

    def forward(self, x, group):
        context = self.context(self.static(group))[:, None]
        context_history = context.expand(-1, x.size(1), -1)
        weights = self.selection(torch.cat([x, context_history], dim=-1)).softmax(-1)
        variables = torch.stack([layer(x[..., i:i + 1]) for i, layer in enumerate(self.variables)], dim=-2)
        history, state = self.encoder((variables * weights[..., None]).sum(dim=-2))
        future = self.horizon(torch.arange(5, device=x.device))[None] + context
        decoded, _ = self.decoder(future, state)
        sequence = self.enrich(torch.cat([history, decoded], dim=1) + context)
        mask = torch.ones(sequence.size(1), sequence.size(1), device=x.device, dtype=torch.bool).triu(1)
        attended, _ = self.attention(sequence, sequence, sequence, attn_mask=mask, need_weights=False)
        return self.output((sequence + attended)[:, -5:])


class Recurrent(nn.Module):
    def __init__(self, features, groups):
        super().__init__()
        self.static = nn.Embedding(groups, 8)
        self.encoder = nn.LSTM(features, 24, batch_first=True)
        self.output = nn.Linear(32, 5)

    def forward(self, x, group):
        hidden, _ = self.encoder(x)
        return self.output(torch.cat([hidden[:, -1], self.static(group)], dim=1))[:, :, None]


def neural(x, y, group, test, test_group, model, epochs):
    torch.manual_seed(606)
    torch.set_num_threads(1)
    median = np.nanmedian(x, axis=(0, 1))
    median = np.nan_to_num(median)
    x = np.where(np.isnan(x), median, x)
    test = np.where(np.isnan(test), median, test)
    scale = x.std(axis=(0, 1)).clip(1e-6)
    tensor = lambda values: torch.as_tensor(values, dtype=torch.float32)
    x, test = tensor((x - median) / scale), tensor((test - median) / scale)
    group, test_group = torch.as_tensor(group), torch.as_tensor(test_group)
    center = np.nanmean(y)
    spread = max(np.nanstd(y), 1e-6)
    y = tensor((y - center) / spread)
    net = (Fusion if model == "TFT" else Recurrent)(x.shape[-1], int(group.max()) + 1)
    optimizer = torch.optim.AdamW(net.parameters(), lr=0.003)
    quantiles = tensor([0.05, 0.50, 0.95])
    for _ in range(epochs):
        for batch in torch.randperm(len(x)).split(64):
            optimizer.zero_grad()
            prediction = net(x[batch], group[batch])
            target = y[batch]
            valid = target.isfinite()
            error = target.nan_to_num()[..., None] - prediction
            if model == "TFT":
                loss = torch.maximum(quantiles * error, (quantiles - 1) * error)[valid].mean()
            else:
                loss = error[valid].square().mean()
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), 1)
            optimizer.step()
    net.eval()
    with torch.no_grad():
        output = net(test, test_group).numpy() * spread + center
    if model == "TFT":
        return output[:, :, 1]
    return output[:, :, 0]
