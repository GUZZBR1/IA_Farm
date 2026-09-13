# Mobile UI Design Specification: IA_Farm

This specification defines the user interface for the IA_Farm Android application, optimized for outdoor agricultural environments.

## 1. Design Philosophy: 'Low-Power / High-Visibility'
The UI is designed for farmers using the app in direct sunlight, often wearing gloves, and needing to conserve battery.

- **Visuals**: 
    - **Contrast**: High-contrast theme (Deep Black backgrounds, High-Visibility Yellow/Green accents).
    - **Typography**: Large, sans-serif fonts (min 16pt) for readability under glare.
    - **Elements**: Oversized touch targets (buttons min 48dp x 48dp) to accommodate clumsy inputs.

## 2. Primary Interface Features
### A. Field-First Input (Voice-to-Text)
- **Central Action Button**: A large, prominent microphone button in the bottom center.
- **STT Integration**: Use Android's `SpeechRecognizer` (Offline mode) to convert voice to text.
- **Visual Feedback**: Waveform animation during recording to indicate the system is listening.

### B. Assistant Output (Text-to-Speech)
- **TTS Integration**: Integrated Android `TextToSpeech` engine to read responses aloud.
- **Audio Toggle**: A simple 'Speaker' icon to toggle audio output on/off.
- **Reading Speed**: Configurable playback speed for different user preferences.

### C. Minimalist Chat View
- **Bubble Design**: Simple, flat bubbles with clear separation.
- **Quick Actions**: Contextual buttons (e.g., "Repeat", "Save to Log", "Send Image") appearing after a response.

## 3. Orchestrator Integration
The UI acts as a thin client communicating with the `orchastrator.py` (converted to a mobile-compatible service or JNI bridge).

- **Input Flow**: 
  `Voice/Text Input` $\rightarrow$ `UI Controller` $\rightarrow$ `Orchestrator API (Local)` $\rightarrow$ `MLC LLM / RAG`
- **Output Flow**:
  `MLC LLM` $\rightarrow$ `Orchestrator` $\rightarrow$ `UI Stream` $\rightarrow$ `Text Display + TTS Engine`
- **State Management**:
  - **Offline Indicator**: A clear status icon showing "Local Mode Active" (No cloud dependency).
  - **Battery Warning**: UI shifts to a "Super-Power-Save" mode (reduced animations, grayscale) when battery < 20%.
