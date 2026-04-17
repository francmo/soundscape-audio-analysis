"""Soundscape Audio Analysis - skill Claude Code per analisi audio soundscape."""
import os

# v0.3.2: abilita fallback CPU per ops PyTorch non supportate su MPS.
# Deve essere settato PRIMA di qualunque import di torch (i moduli della skill
# fanno import lazy, quindi questo setdefault è la prima occasione utile).
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

__version__ = "0.6.5"
