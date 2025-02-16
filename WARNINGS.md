# ScriptRunContext Warnings

The following warnings:
```
2025-02-16 15:09:52.675 Thread 'ThreadPoolExecutor-7_0': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-02-16 15:09:52.675 Thread 'ThreadPoolExecutor-7_0': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-02-16 15:10:22.821 Thread 'ThreadPoolExecutor-8_0': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-02-16 15:10:22.823 Thread 'ThreadPoolExecutor-8_0': missing ScriptRunContext! This warning can be ignored when running in bare mode.
```

are generated because the dummy `ScriptRunContext` functions (provided as a fallback) do not attach any context. They are expected when running the application outside of the full Streamlit runtime.

If you're running the app in bare mode (for example, using a command-line or a non-Streamlit environment), these warnings can safely be ignored.

In a production environment or when working within Streamlit’s runtime, consider implementing or importing the proper `ScriptRunContext` functions to avoid these messages.
