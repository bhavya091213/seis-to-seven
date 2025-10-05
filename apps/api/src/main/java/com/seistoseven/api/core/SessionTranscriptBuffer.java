package com.seistoseven.api.core;

import com.seistoseven.api.dto.TranscriptEntry;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.atomic.AtomicInteger;

public class SessionTranscriptBuffer {
    private final ConcurrentLinkedDeque<TranscriptEntry> entries = new ConcurrentLinkedDeque<>();
    private final AtomicInteger nextId = new AtomicInteger(1);

    public void append(double t, double dur, String speaker, String lang, String text) {
        int id = nextId.getAndIncrement();
        entries.addLast(new TranscriptEntry(id, t, dur, speaker, lang, text));
    }

    public List<TranscriptEntry> snapshot() {
        return List.copyOf(entries);
    }

    public void clear() {
        entries.clear();
        nextId.set(1);
    }
}
