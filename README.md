# 🦆 Uberduck TTS ![](https://img.shields.io/github/forks/uberduck-ai/uberduck-ml-dev) ![](https://img.shields.io/github/stars/uberduck-ai/uberduck-ml-dev) ![](https://img.shields.io/github/issues/uberduck-ai/uberduck-ml-dev)



<h1>Table of Contents<span class="tocSkip"></span></h1>
<div class="toc"><ul class="toc-item"><li><span><a href="#🦆-Uberduck-TTS---" data-toc-modified-id="🦆-Uberduck-TTS----1"><span class="toc-item-num">1&nbsp;&nbsp;</span>🦆 Uberduck TTS <img src="https://img.shields.io/github/forks/uberduck-ai/uberduck-ml-dev" alt=""> <img src="https://img.shields.io/github/stars/uberduck-ai/uberduck-ml-dev" alt=""> <img src="https://img.shields.io/github/issues/uberduck-ai/uberduck-ml-dev" alt=""></a></span><ul class="toc-item"><li><span><a href="#Installation" data-toc-modified-id="Installation-1.1"><span class="toc-item-num">1.1&nbsp;&nbsp;</span>Installation</a></span></li><li><span><a href="#Development" data-toc-modified-id="Development-1.2"><span class="toc-item-num">1.2&nbsp;&nbsp;</span>Development</a></span><ul class="toc-item"><li><span><a href="#🚩-Testing" data-toc-modified-id="🚩-Testing-1.2.1"><span class="toc-item-num">1.2.1&nbsp;&nbsp;</span>🚩 Testing</a></span></li></ul></li><li><span><a href="#📦️-nbdev" data-toc-modified-id="📦️-nbdev-1.3"><span class="toc-item-num">1.3&nbsp;&nbsp;</span>📦️ nbdev</a></span><ul class="toc-item"><li><span><a href="#🔧-Troubleshooting-Tips" data-toc-modified-id="🔧-Troubleshooting-Tips-1.3.1"><span class="toc-item-num">1.3.1&nbsp;&nbsp;</span>🔧 Troubleshooting Tips</a></span></li></ul></li><li><span><a href="#Overview" data-toc-modified-id="Overview-1.4"><span class="toc-item-num">1.4&nbsp;&nbsp;</span>Overview</a></span></li></ul></li></ul></div>

[**Uberduck**](https://uberduck.ai/) is a tool for fun and creativity with audio machine learning, currently focused on voice cloning and neural text-to-speech. This repository includes development tools to get started with creating your own speech synthesis model. For more information on the state of this repo, please see the [**Wiki**](https://github.com/uberduck-ai/uberduck-ml-dev/wiki).

## Installation

```
conda create -n 'uberduck-ml-dev' python=3.8
source activate uberduck-ml-dev
pip install git+git://github.com/uberduck-ai/uberduck-ml-dev 
```

## Development

To start contributing, install the required development dependencies in a virtual environment:

```bash
pip install nbdev==1.1.22 nbqa==1.1.1 pre-commit
```

Then install required Git hooks:

```bash
nbdev_install_git_hooks
pre-commit install
```

All development takes place in Jupyter notebooks in `$REPO_ROOT/nbs`, which are compiled to library code in `$REPO_ROOT/uberduck_ml_dev`. To make changes, edit edit the one of the IPython notebooks in `$REPO_ROOT/nbs/` after starting a jupyter server with `jupyter notebook`. Once you're satisfied with the changes, build them:

```bash
./build_lib
```

Then install the library
```bash
python setup.py develop
```

### 🚩 Testing

Any IPython notebook cell which is not exported is a test. Run all tests:

```bash
nbdev_test_nbs
```

Test a single notebook:

```bash
 nbdev_test_nbs --fname nbs/text.util.ipynb
 ```
 (can optionally add `--verbose` for more output)
 
 Annotate a notebook cell with the `#skip` flag if it is code which is neither a test nor library code.

## 📦️ nbdev

This project uses [nbdev](https://nbdev.fast.ai/).

_If you are using an older version of this template, and want to upgrade to the theme-based version, see [this helper script](https://gist.github.com/hamelsmu/977e82a23dcd8dcff9058079cb4a8f18) (more explanation of what this means is contained in the link to the script)_.

### 🔧 Troubleshooting Tips

-  Make sure you are using the latest version of nbdev with `pip install -U nbdev`
-  If you are using an older version of this template, see the instructions above on how to upgrade your template. 
-  It is important for you to spell the name of your user and repo correctly in `settings.ini` or the website will not have the correct address from which to source assets like CSS for your site.  When in doubt, you can open your browser's developer console and see if there are any errors related to fetching assets for your website due to an incorrect URL generated by misspelled values from `settings.ini`.
-  If you change the name of your repo, you have to make the appropriate changes in `settings.ini`
-  After you make changes to `settings.ini`, run `nbdev_build_lib && nbdev_clean_nbs && nbdev_build_docs` to make sure all changes are propagated appropriately.


## Overview

An overview of the subpackages in this library:

`models`: TTS model implementations. All models descend from `models.base.TTSModel`.

`trainer`: A trainer has logic for training a model.

`exec`: Contains entrypoint scripts for running training jobs. Executed via a command like
`python -m uberduck_ml_dev.exec.train_tacotron2 --your-args here`
