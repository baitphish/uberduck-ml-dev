__all__ = [
    "get_summary_statistics",
    "calculate_statistics",
    "generate_markdown",
    "parse_args",
    "run",
]


import argparse
import os
import sys
from typing import List, Any, Dict
import json

from g2p_en import G2p
import librosa
import math
import matplotlib.pyplot as plt
from mdutils.mdutils import MdUtils
import numpy as np
from pydub import AudioSegment, silence
import seaborn as sns
from tqdm import tqdm

from ..data.statistics import (
    AbsoluteMetrics,
    count_frequency,
    create_wordcloud,
    get_sample_format,
    pace_character,
    pace_phoneme,
    word_frequencies,
)
from ..text.util import clean_text, text_to_sequence
from ..utils.audio import compute_yin


def get_summary_statistics(arr):
    if len(arr) == 0:
        return {}
    arr_np = np.array(arr)
    return {
        "p10": float(np.percentile(arr_np, 10)),
        "p25": float(np.percentile(arr_np, 25)),
        "p50": float(np.percentile(arr_np, 50)),
        "p75": float(np.percentile(arr_np, 75)),
        "p90": float(np.percentile(arr_np, 90)),
        "max": float(np.max(arr_np)),
        "min": float(np.min(arr_np)),
    }


def calculate_statistics(
    dataset_path, input_file, output_folder, delimiter, metrics=True, wordcloud=True
):
    n_clips = 0
    sample_rates = {}
    channels = {"mono": 0, "stereo": 0}
    extensions = {}
    sample_formats = {}
    total_lengths = []
    leading_silence_lengths = []
    trailing_silence_lengths = []
    paces_characters = []  # number of characters / seconds in audio clip
    paces_phonemes = []  # number of phonemes / seconds in audio clip
    lookup_results = {
        "RNN": [],
        "CMU": [],
        "non-alphanumeric": [],
        "homograph": [],
    }  # keep track of how arpabet sequences were generated
    mosnet_scores = []
    srmr_scores = []
    word_freqs = []
    all_words = []
    all_pitches = np.array([])
    all_loudness = []

    g2p = G2p()
    files_with_error = []
    if metrics:
        abs_metrics = AbsoluteMetrics()

    with open(os.path.join(dataset_path, input_file)) as transcripts:
        for line in tqdm(transcripts.readlines()):
            try:
                line = line.strip()  # remove trailing newline character
                file, transcription = line.lower().split(delimiter)
                transcription_cleaned = clean_text(transcription, ["english_cleaners"])

                _, file_extension = os.path.splitext(file)
                path_to_file = os.path.join(dataset_path, file)
                file_pydub = AudioSegment.from_wav(path_to_file)
                data_np, _ = librosa.load(path_to_file)

                # Format Metadata
                sr = file_pydub.frame_rate
                if sr in sample_rates.keys():
                    sample_rates[sr] += 1
                else:
                    sample_rates[sr] = 1

                if file_pydub.channels == 1:
                    channels["mono"] += 1
                else:
                    channels["stereo"] += 1

                if file_extension in extensions.keys():
                    extensions[file_extension] += 1
                else:
                    extensions[file_extension] = 1

                fmt = get_sample_format(path_to_file)
                if fmt in sample_formats.keys():
                    sample_formats[fmt] += 1
                else:
                    sample_formats[fmt] = 1

                # lengths
                total_lengths.append(file_pydub.duration_seconds)
                leading_silence_lengths.append(
                    silence.detect_leading_silence(file_pydub)
                )
                trailing_silence_lengths.append(
                    silence.detect_leading_silence(file_pydub.reverse())
                )

                # Paces
                paces_phonemes.append(
                    pace_phoneme(text=transcription_cleaned, audio=path_to_file)
                )
                paces_characters.append(
                    pace_character(text=transcription_cleaned, audio=path_to_file)
                )

                # Pitch
                pitches, harmonic_rates, argmins, times = compute_yin(data_np, sr=sr)
                pitches = np.array(pitches)
                pitches = pitches[pitches > 10]
                all_pitches = np.append(all_pitches, pitches)

                # Loudness
                all_loudness.append(file_pydub.dBFS)

                # Quality
                if metrics:
                    scores = abs_metrics(path_to_file)
                    mosnet_scores.append(scores["mosnet"][0][0])
                    srmr_scores.append(scores["srmr"])

                # Transcription
                word_freqs.extend(word_frequencies(transcription_cleaned))
                transcription_lookups = g2p.check_lookup(transcription_cleaned)
                for k in transcription_lookups:
                    lookup_results[k].extend(transcription_lookups[k])

                all_words.append(transcription_cleaned)

                n_clips += 1
            except Exception as e:
                print(e)
                files_with_error.append(file)

    if n_clips == 0:
        return None

    if wordcloud:
        create_wordcloud(
            " ".join(all_words),
            os.path.join(dataset_path, output_folder, "wordcloud.png"),
        )

    # Length graph
    plt.clf()
    sns.histplot(total_lengths)
    plt.title("Audio length distribution")
    plt.xlabel("Audio length (s)")
    plt.ylabel("Count")
    plt.savefig(os.path.join(dataset_path, output_folder, "lengths.png"))

    # Word Frequencies graph
    plt.clf()
    sns.histplot(word_freqs, bins=10)
    plt.title("Word frequency distribution [0-1]")
    plt.xlabel("Word frequency")
    plt.ylabel("Count")
    plt.savefig(os.path.join(dataset_path, output_folder, "word_frequencies.png"))
    plt.close()

    # Pitches graph
    plt.clf()
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    sns.histplot(all_pitches)
    plt.title("Pitch distribution")
    plt.xlabel("Fundamental Frequency (Hz)")
    plt.ylabel("Count")
    plt.subplot(1, 2, 2)
    sns.histplot(all_loudness)
    plt.title("Loudness distribution")
    plt.xlabel("Loudness (dBFS)")
    plt.ylabel("Count")
    plt.savefig(os.path.join(dataset_path, output_folder, "pitch_loudness.png"))
    plt.close()

    # Silences graph
    plt.clf()
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    sns.histplot(leading_silence_lengths)
    plt.title("Leading silence distribution")
    plt.xlabel("Leading silence (ms)")
    plt.ylabel("Count")
    plt.subplot(1, 2, 2)
    sns.histplot(trailing_silence_lengths)
    plt.title("Traling silence distribution")
    plt.xlabel("Trailing silence (ms)")
    plt.ylabel("Count")
    plt.savefig(os.path.join(dataset_path, output_folder, "silences.png"))
    plt.close()

    # Metrics graph
    plt.clf()
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    sns.histplot(mosnet_scores)
    plt.title("Mosnet score distribution")
    plt.xlabel("Mosnet score")
    plt.ylabel("Count")
    plt.subplot(1, 2, 2)
    sns.histplot(srmr_scores)
    plt.title("SRMR score distribution")
    plt.xlabel("SRMR score")
    plt.ylabel("Count")
    plt.savefig(os.path.join(dataset_path, output_folder, "metrics.png"))
    plt.close()

    # Paces graph
    plt.clf()
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    sns.histplot(paces_characters)
    plt.title("Pace (chars/s)")
    plt.xlabel("Characters / second")
    plt.ylabel("Count")
    plt.subplot(1, 2, 2)
    sns.histplot(paces_phonemes)
    plt.title("Pace (phonemes/s)")
    plt.xlabel("Phonemes / second")
    plt.ylabel("Count")
    plt.savefig(os.path.join(dataset_path, output_folder, "paces.png"))
    plt.close()

    return {
        "n_clips": n_clips,
        "total_lengths_summary": get_summary_statistics(total_lengths),
        "paces_phonemes_summary": get_summary_statistics(paces_phonemes),
        "paces_characters_summary": get_summary_statistics(paces_characters),
        "mosnet_scores_summary": get_summary_statistics(mosnet_scores),
        "srmr_scores_summary": get_summary_statistics(srmr_scores),
        "pitch_summary": get_summary_statistics(all_pitches),
        "loudness_summary": get_summary_statistics(all_loudness),
        "total_lengths": total_lengths,
        "paces_phonemes": paces_phonemes,
        "paces_characters": paces_characters,
        "mosnet_scores": mosnet_scores,
        "srmr_scores": srmr_scores,
        "sample_rates": sample_rates,
        "channels": channels,
        "extensions": extensions,
        "sample_formats": sample_formats,
        "lookup_results": lookup_results,
        "files_with_error": files_with_error,
    }


def generate_markdown(output_file, dataset_path, output_folder, data):
    mdFile = MdUtils(
        file_name=os.path.join(dataset_path, output_file), title=f"Dataset statistics"
    )

    total_length_mins = sum(data["total_lengths"]) / 60.0
    mdFile.new_header(level=1, title="Overview")
    mdFile.new_line(f"**Number of clips:** {data['n_clips']}")
    mdFile.new_line(
        f"**Total data:** {math.floor(total_length_mins)} minutes {math.ceil(total_length_mins % 1 * 60.0)} seconds"
    )
    mdFile.new_line(
        f"**Mean clip length:** {sum(data['total_lengths'])/data['n_clips']:.2f} seconds"
    )
    mdFile.new_line(
        f"**Mean pace:** {sum(data['paces_phonemes'])/len(data['paces_phonemes']):.2f} \
            phonemes/sec {sum(data['paces_characters'])/len(data['paces_characters']):.2f} chars/sec"
    )
    if len(data["mosnet_scores"]) > 0:
        mdFile.new_line(
            f"**Mean MOSNet:** {sum(data['mosnet_scores'])/len(data['mosnet_scores']):.2f}"
        )
        mdFile.new_line(
            f"**Mean SRMR:** {sum(data['srmr_scores'])/len(data['srmr_scores']):.2f}"
        )

    if len(data["files_with_error"]) > 0:
        mdFile.new_line(f"**Errored Files:** {', '.join(data['files_with_error'])}")

    list_of_strings = ["Sample Rate (Hz)", "Count"]
    for k in data["sample_rates"].keys():
        list_of_strings.extend([str(k), str(data["sample_rates"][k])])
    mdFile.new_table(
        columns=2,
        rows=len(data["sample_rates"].keys()) + 1,
        text=list_of_strings,
        text_align="center",
    )

    list_of_strings = ["Audio Type", "Count"]
    n_rows = 1
    for k in data["channels"].keys():
        if data["channels"][k] > 0:
            n_rows += 1
            list_of_strings.extend([str(k), str(data["channels"][k])])
    mdFile.new_table(columns=2, rows=n_rows, text=list_of_strings, text_align="center")

    list_of_strings = ["Audio Format", "Count"]
    for k in data["extensions"].keys():
        list_of_strings.extend([str(k), str(data["extensions"][k])])
    mdFile.new_table(
        columns=2,
        rows=len(data["extensions"].keys()) + 1,
        text=list_of_strings,
        text_align="center",
    )

    list_of_strings = ["Sample Format", "Count"]
    for k in data["sample_formats"].keys():
        list_of_strings.extend([str(k), str(data["sample_formats"][k])])
    mdFile.new_table(
        columns=2,
        rows=len(data["sample_formats"].keys()) + 1,
        text=list_of_strings,
        text_align="center",
    )

    list_of_strings = ["Arpabet Lookup Type", "Count"]
    for k in data["lookup_results"].keys():
        list_of_strings.extend([str(k), str(len(data["lookup_results"][k]))])
    mdFile.new_table(
        columns=2,
        rows=len(data["lookup_results"].keys()) + 1,
        text=list_of_strings,
        text_align="center",
    )
    mdFile.new_line(
        mdFile.new_inline_image(
            text="Wordcloud", path=os.path.join(output_folder, "wordcloud.png")
        )
    )
    mdFile.new_line(
        mdFile.new_inline_image(
            text="Audio Lengths", path=os.path.join(output_folder, "lengths.png")
        )
    )
    mdFile.new_line(
        mdFile.new_inline_image(
            text="Paces", path=os.path.join(output_folder, "paces.png")
        )
    )
    mdFile.new_line(
        mdFile.new_inline_image(
            text="Silences", path=os.path.join(output_folder, "silences.png")
        )
    )
    if len(data["mosnet_scores"]) > 0:
        mdFile.new_line(
            mdFile.new_inline_image(
                text="Metrics", path=os.path.join(output_folder, "metrics.png")
            )
        )
    mdFile.new_line(
        mdFile.new_inline_image(
            text="Word Frequencies",
            path=os.path.join(output_folder, "word_frequencies.png"),
        )
    )
    mdFile.new_line(
        mdFile.new_inline_image(
            text="Pitch and Loudness",
            path=os.path.join(output_folder, "pitch_loudness.png"),
        )
    )

    rnn_frequency_counts = count_frequency(data["lookup_results"]["RNN"])

    list_of_strings = ["Frequently Missed Words", "Count"]
    n_rows = 0
    for k in rnn_frequency_counts.keys():
        if rnn_frequency_counts[k] > 1:
            n_rows += 1
            list_of_strings.extend([str(k), str(rnn_frequency_counts[k])])
    mdFile.new_table(
        columns=2,
        rows=n_rows + 1,
        text=list_of_strings,
        text_align="center",
    )

    mdFile.new_line(
        f'**Words not found in CMU:** {", ".join(data["lookup_results"]["RNN"])}'
    )
    mdFile.create_md_file()


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--dataset_path", help="Path to the dataset.", type=str, required=True
    )
    parser.add_argument(
        "-i",
        "--input_file",
        help="Path to the transcription file.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output_file",
        help="Markdown file to write statistics to.",
        type=str,
        default="README",
    )
    parser.add_argument(
        "--output_folder",
        help="Folder to save plots and images.",
        type=str,
        default="stats",
    )
    parser.add_argument(
        "--delimiter", help="Transcription file delimiter.", type=str, default="|"
    )
    parser.add_argument("--metrics", dest="metrics", action="store_true")
    parser.add_argument("--no-metrics", dest="metrics", action="store_false")
    parser.add_argument("--wordcloud", dest="wordcloud", action="store_true")
    parser.add_argument("--no-wordcloud", dest="wordcloud", action="store_false")
    parser.set_defaults(metrics=True, wordcloud=True)
    return parser.parse_args(args)


def run(
    dataset_path, input_file, output_file, output_folder, delimiter, metrics, wordcloud
):
    if not os.path.exists(os.path.join(dataset_path, input_file)):
        raise Exception(
            f"Transcription file {os.path.join(dataset_path,input_file)} does not exist"
        )

    os.makedirs(os.path.join(dataset_path, output_folder), exist_ok=True)
    data = calculate_statistics(
        dataset_path, input_file, output_folder, delimiter, metrics, wordcloud
    )
    if data:
        generate_markdown(output_file, dataset_path, output_folder, data)
        with open(os.path.join(dataset_path, "stats.json"), "w") as outfile:
            keys = [
                "n_clips",
                "total_lengths_summary",
                "paces_phonemes_summary",
                "paces_characters_summary",
                "mosnet_scores_summary",
                "srmr_scores_summary",
                "pitch_summary",
                "loudness_summary",
                "sample_rates",
                "channels",
                "extensions",
                "sample_formats",
            ]
            json_data = {k: data[k] for k in keys}
            json_data["arpabet_rnn"] = data["lookup_results"]["RNN"]
            json.dump(json_data, outfile, indent=2)


try:
    from nbdev.imports import IN_NOTEBOOK
except:
    IN_NOTEBOOK = False

if __name__ == "__main__" and not IN_NOTEBOOK:
    args = parse_args(sys.argv[1:])

    if os.path.exists(
        os.path.join(args.dataset_path, args.output_file)
    ) or os.path.exists(os.path.join(args.dataset_path, args.output_file + ".md")):
        inp = input(
            f"This script will overwite everything in the {args.output_file} file with dataset statistics. Would you like to continue? (y/n) "
        ).lower()
        if inp != "y":
            print("Not calculating statistics...")
            print("HINT: Use -o/--output-file to specify a new markdown file name")
            sys.exit()
    print("Calculating statistics...")
    run(
        args.dataset_path,
        args.input_file,
        args.output_file,
        args.output_folder,
        args.delimiter,
        args.metrics,
        args.wordcloud,
    )
