# Architecture

## Layers

### CLI
Parses user intent and builds a request object.

### Extraction
Dispatches by input format and reads logical pages, tables, and segments.

- `.pdf` uses `PyMuPDF`;
- `.docx` uses `python-docx` and splits pages only by explicit manual page breaks;
- `.md` and `.txt` are treated as single logical-page text documents.

### Normalization
Cleans raw PDF text into speech-friendly Russian text.

### TTS engine
Receives normalized text and writes WAV.

### Audio post-processing
Converts WAV to mp3/m4a and concatenates segments if required.

### Pipeline
Coordinates the whole flow.

## First implementation target

```text
Input document -> selected logical pages -> normalized page text -> Silero/Piper WAV -> ffmpeg export
```

## Future extensions

- region-based extraction;
- separate table audio;
- chapter-aware splitting;
- caching of extracted text;
- alternative local TTS engine;
- richer `.docx` pagination via external renderer if it is ever worth the extra system dependency.
