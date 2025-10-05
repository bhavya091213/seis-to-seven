package com.seistoseven.api.dto;

public record TranscriptEntry(
    int id,          // assigned server-side
    double t,        // seconds since session start
    double dur,      // optional duration
    String speaker,  // "A" or "B"
    String lang,     // "en", "es", ...
    String text
) {}
