# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/utils.utils.ipynb (unless otherwise specified).

__all__ = ['load_filepaths_and_text', 'synthesize_speakerids2', 'parse_vctk', 'parse_libritts_mellotron',
           'load_filepaths_and_text', 'add_speakerid', 'parse_libritts_mellotron', 'parse_uberduck', 'parse_ljspeech',
           'window_sumsquare', 'griffin_lim', 'dynamic_range_compression', 'dynamic_range_decompression', 'to_gpu',
           'get_mask_from_lengths', 'reduce_tensor']

# Cell

import sys
import os
import soundfile as sf
import pandas as pd

import numpy as np

import soundfile as sf
import librosa


def load_filepaths_and_text(dataset_path: str, filename: str, split: str = "|"):
    with open(filename, encoding="utf-8") as f:
        filepaths_and_text = [line.strip().split(split) for line in f]
    return filepaths_and_text


def synthesize_speakerids2(filelists, fix_indices_index=None):

    data_dict = {}
    data_dict_out = {}
    for f in range(len(filelists)):
        data = load_filepaths_and_text(filelists[f])
        data_dict[filelists[f]] = pd.DataFrame(data)

    source_files = list(data_dict.keys())

    speaker_offset = {}
    nfilelist = len(filelists)
    reserved_speakers = np.unique(data_dict[filelists[fix_indices_index]].iloc[:, 2])

    for s in range(nfilelist):
        source_file = filelists[s]
        data = data_dict[source_file]
        if s != fix_indices_index:
            speakers = np.unique(data.iloc[:, 2])
            overlap = np.where(np.isin(speakers, reserved_speakers))[0]
            reserved_speakers_temp = np.union1d(speakers, reserved_speakers)
            newindices = np.setdiff1d(
                list(range(len(reserved_speakers) + len(speakers))),
                reserved_speakers_temp,
            )[: len(overlap)]
            for o in range(len(overlap)):
                data.iloc[np.where(data.iloc[:, 2] == overlap[o])[0], 2] = newindices[o]

            data_dict_out[source_file] = data
            speakers = np.unique(data.iloc[:, 2])
            reserved_speakers = np.union1d(speakers, reserved_speakers)
        else:
            data_dict_out[source_file] = data
    return data_dict_out

def parse_vctk(root):
    """Parse VCTK dataset and return a dict representation."""
    wav_dir = os.path.join(root, "wav48_silence_trimmed")
    txt_dir = os.path.join(root, "txt")
    speaker_wavs = os.listdir(wav_dir)
    speaker_txts = os.listdir(txt_dir)
    speakers = list(set(speaker_wavs) & set(speaker_txts))
    output_dict = {}
    for speaker in speakers:
        speaker_wav_dir = os.path.join(wav_dir, speaker)
        speaker_txt_dir = os.path.join(txt_dir, speaker)
        wav_files_speaker = np.asarray(os.listdir(speaker_wav_dir))
        txt_files_speaker = np.asarray(os.listdir(speaker_txt_dir))

        nwavfiles = len(wav_files_speaker)

        transcription_basenames = np.asarray([t[:8] for t in txt_files_speaker])
        audio_basenames = np.asarray([w[:8] for w in wav_files_speaker])
        mic = np.asarray([w[12] for w in wav_files_speaker])
        mic1_ind = mic == "1"
        wav_files_speaker = wav_files_speaker[mic1_ind]
        audio_basenames = audio_basenames[mic1_ind]

        combined_files = np.intersect1d(transcription_basenames, audio_basenames)
        matching_inds1 = np.where(np.isin(transcription_basenames, combined_files))[0]
        matching_inds2 = np.where(np.isin(audio_basenames, combined_files))[0]
        inds1 = matching_inds1[transcription_basenames[matching_inds1].argsort()]
        inds2 = matching_inds2[audio_basenames[matching_inds2].argsort()]
        txt_files_speaker = txt_files_speaker[inds1]
        wav_files_speaker = wav_files_speaker[inds2]
        texts, wavs = [], []
        for text_basename, wav_basename in zip(txt_files_speaker, wav_files_speaker):
            text_file = os.path.join(speaker_txt_dir, text_basename)
            with open(text_file) as f:
                contents = f.read().strip("\n")
            texts.append(contents)
            wav_file = os.path.join(speaker_wav_dir, wav_basename)
            wavs.append(wav_file)

        if len(wavs):
            output_dict[speaker] = list(zip(texts, wavs))
    return output_dict


def parse_libritts_mellotron(source_folder, mellotron_filelist):

    data = pd.read_csv(mellotron_filelist, sep="|", header=None, error_bad_lines=False)

    data[0] = data[0].str[17:]

    data[0] = source_folder + data[0].astype(str)
    return data


def load_filepaths_and_text(filename, split="|"):
    with open(filename, encoding="utf-8") as f:
        filepaths_and_text = [line.strip().split(split) for line in f]
    return filepaths_and_text


def add_speakerid(data, speaker_key=0):

    if data.shape[1] == 3:
        if type(data[2]) == int:
            pass
        else:
            speaker_ids = np.asarray(
                np.ones(data.shape[0], dtype=int) * speaker_key, dtype=int
            )
            data[2] = speaker_ids
    if data.shape[1] == 2:
        speaker_ids = np.asarray(
            np.ones(data.shape[0], dtype=int) * speaker_key, dtype=int
        )
        data[2] = speaker_ids

    return data


def parse_libritts_mellotron(source_folder, mellotron_filelist):

    data = load_filepaths_and_text(mellotron_filelist)
    data = pd.DataFrame(data)
    data[0] = data[0].str[17:]

    data[0] = source_folder + data[0].astype(str)
    return data


def parse_uberduck(source_folder):

    source_file = source_folder + "/all.txt"
    data = load_filepaths_and_text(source_file)
    data = pd.DataFrame(data)

    nsamp = data.shape[0]
    data[0] = source_folder + "/" + data[0].astype(str)
    output = add_speakerid(data, speaker_key=0)

    for i in range(output.shape[0]):
        loaded = librosa.load(output.iloc[i, 0])
        sf.write(output.iloc[i, 0], loaded[0], loaded[1])

    return output


def parse_ljspeech(source_folder):

    source_file = source_folder + "/metadata.csv"
    data = load_filepaths_and_text(source_file)
    data = pd.DataFrame(data)
    nsamp = data.shape[0]

    data[0] = source_folder + "/wavs/" + data[0].astype(str)
    output = add_speakerid(data, speaker_key=0)
    for i in range(output.shape[0]):
        output.iloc[i, 0] = output.iloc[i, 0] + ".wav"

    return output

# Cell

import torch
import numpy as np
from scipy.signal import get_window
import librosa.util as librosa_util


def window_sumsquare(window, n_frames, hop_length=200, win_length=800,
                     n_fft=800, dtype=np.float32, norm=None):
    """
    # from librosa 0.6
    Compute the sum-square envelope of a window function at a given hop length.

    This is used to estimate modulation effects induced by windowing
    observations in short-time fourier transforms.

    Parameters
    ----------
    window : string, tuple, number, callable, or list-like
        Window specification, as in `get_window`

    n_frames : int > 0
        The number of analysis frames

    hop_length : int > 0
        The number of samples to advance between frames

    win_length : [optional]
        The length of the window function.  By default, this matches `n_fft`.

    n_fft : int > 0
        The length of each analysis frame.

    dtype : np.dtype
        The data type of the output

    Returns
    -------
    wss : np.ndarray, shape=`(n_fft + hop_length * (n_frames - 1))`
        The sum-squared envelope of the window function
    """
    if win_length is None:
        win_length = n_fft

    n = n_fft + hop_length * (n_frames - 1)
    x = np.zeros(n, dtype=dtype)

    # Compute the squared window at the desired length
    win_sq = get_window(window, win_length, fftbins=True)
    win_sq = librosa_util.normalize(win_sq, norm=norm)**2
    win_sq = librosa_util.pad_center(win_sq, n_fft)

    # Fill the envelope
    for i in range(n_frames):
        sample = i * hop_length
        x[sample:min(n, sample + n_fft)] += win_sq[:max(0, min(n_fft, n - sample))]
    return x


def griffin_lim(magnitudes, stft_fn, n_iters=30):
    """
    PARAMS
    ------
    magnitudes: spectrogram magnitudes
    stft_fn: STFT class with transform (STFT) and inverse (ISTFT) methods
    """

    angles = np.angle(np.exp(2j * np.pi * np.random.rand(*magnitudes.size())))
    angles = angles.astype(np.float32)
    angles = torch.autograd.Variable(torch.from_numpy(angles))
    signal = stft_fn.inverse(magnitudes, angles).squeeze(1)

    for i in range(n_iters):
        _, angles = stft_fn.transform(signal)
        signal = stft_fn.inverse(magnitudes, angles).squeeze(1)
    return signal


def dynamic_range_compression(x, C=1, clip_val=1e-5):
    """
    PARAMS
    ------
    C: compression factor
    """
    return torch.log(torch.clamp(x, min=clip_val) * C)


def dynamic_range_decompression(x, C=1):
    """
    PARAMS
    ------
    C: compression factor used to compress
    """
    return torch.exp(x) / C


# Cell
def to_gpu(x):
    x = x.contiguous()

    if torch.cuda.is_available():
        x = x.cuda(non_blocking=True)
    return torch.autograd.Variable(x)

# Cell

def get_mask_from_lengths(lengths):
    """Return a mask matrix. Unmasked entires are true."""
    max_len = torch.max(lengths).item()
    tensor_cls = torch.cuda.LongTensor if isinstance(lengths,torch.cuda.LongTensor) else torch.LongTensor
    ids = torch.arange(0, max_len, out=tensor_cls(max_len))
    mask = (ids < lengths.unsqueeze(1)).bool()
    return mask

# Cell
import torch.distributed as dist

def reduce_tensor(tensor, n_gpus):
    rt = tensor.clone()
    dist.all_reduce(rt, op=dist.ReduceOp.SUM)
    rt /= n_gpus
    return rt
