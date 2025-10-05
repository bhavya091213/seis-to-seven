package com.seistoseven.api.controllers;

import com.seistoseven.api.core.SessionStore;
import com.seistoseven.api.core.SessionTranscriptBuffer;
import com.seistoseven.api.core.SummaryService;
import com.seistoseven.api.dto.AppendEntryRequest;
import com.seistoseven.api.dto.SummaryRequest;
import com.seistoseven.api.dto.SummaryResponse;
import com.seistoseven.api.dto.TranscriptEntry;

import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/session")
public class SummaryController {
    private final SessionStore store;
    private final SummaryService summaryService;

    public SummaryController(SessionStore store, SummaryService summaryService) {
        this.store = store;
        this.summaryService = summaryService;
    }

    @PostMapping("/{id}/entry")
    public Map<String, Object> appendEntry(@PathVariable String id, @RequestBody AppendEntryRequest req) {
        SessionTranscriptBuffer buf = store.getOrCreate(id);
        buf.append(req.t(), req.dur(), req.speaker(), req.lang(), req.text());
        return Map.of("status", "ok");
    }

    @GetMapping("/{id}/entries")
    public List<TranscriptEntry> listEntries(@PathVariable String id) {
        return store.getOrCreate(id).snapshot();
    }

    @PostMapping("/{id}/summary")
    public SummaryResponse summarize(@PathVariable String id, @RequestBody SummaryRequest req) throws Exception {
        SessionTranscriptBuffer buf = store.get(id);
        if (buf == null) throw new IllegalArgumentException("Unknown session: " + id);
        String summaryText = summaryService.summarize(buf.snapshot(), req.targetLang());
        return new SummaryResponse(summaryText);
    }

    @DeleteMapping("/{id}")
    public Map<String, Object> endSession(@PathVariable String id) {
        SessionTranscriptBuffer buf = store.get(id);
        if (buf != null) buf.clear();
        store.remove(id);
        return Map.of("status", "ended");
    }
}
