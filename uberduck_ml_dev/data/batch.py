from typing import Dict

from ..utils.utils import to_gpu


class Batch(Dict):
    # NOTE (Sam): isn't gate target redundant to output length.
    # NOTE (Sam): here types are unused, but TypedDict inheritance doesn't allow methods
    # NOTE (Sam): these were also problems with object (I forget), NamedTuple (mutability), dataclass (I forget)

    # text_int_padded: Optional[torch.LongTensor] = None
    # input_lengths: Optional[torch.LongTensor] = None
    # mel_padded: Optional[torch.FloatTensor] = None  # for teacher forcing.
    # gate_target: Optional[
    #     torch.LongTensor
    # ] = None  # NOTE (Sam): could be bool -  for teacher forcing.
    # output_lengths: Optional[torch.LongTensor] = None
    # speaker_ids: Optional[torch.LongTensor] = None
    # gst: Optional[torch.Tensor] = None
    # mel_outputs: Optional[torch.Tensor] = None  # predicted.
    # mel_outputs_postnet: Optional[torch.Tensor] = None
    # gate_predicted: Optional[torch.LongTensor] = None  # could be bool.
    # alignments: Optional[torch.Tensor] = None
    # audio_encodings: Optional[torch.Tensor] = None

    def subset(self, keywords, fragile=False) -> "Batch":
        d = {}
        for k in keywords:
            try:
                d[k] = self[k]
            except KeyError:
                if fragile:
                    raise
        return Batch(**d)

    def to_gpu(self) -> "Batch":

        batch_gpu = Batch(**{k: to_gpu(v) for k, v in self.items()})
        return batch_gpu
