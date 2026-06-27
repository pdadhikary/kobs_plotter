"""
UI layer for kobs-plotter.

Contains PySide6 panel and window components. All UI state flows through
a shared PlotSettingsBuilder instance which is finalised into an immutable
PlotSettings object when the user triggers computation.
"""
