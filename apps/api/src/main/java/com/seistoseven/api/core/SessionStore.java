package com.seistoseven.api.core;

import org.springframework.stereotype.Component;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class SessionStore {
    private final Map<String, SessionTranscriptBuffer> sessions = new ConcurrentHashMap<>();

    public SessionTranscriptBuffer getOrCreate(String sessionId) {
        return sessions.computeIfAbsent(sessionId, id -> new SessionTranscriptBuffer());
    }

    public SessionTranscriptBuffer get(String sessionId) {
        return sessions.get(sessionId);
    }

    public void remove(String sessionId) {
        sessions.remove(sessionId);
    }
}
