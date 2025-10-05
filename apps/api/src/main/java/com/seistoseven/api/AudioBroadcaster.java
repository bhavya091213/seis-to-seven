package com.seistoseven.api;

import org.springframework.stereotype.Service;
import org.springframework.web.socket.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class AudioBroadcaster {
    // streamId -> sessions
    private final Map<String, Set<WebSocketSession>> streams = new ConcurrentHashMap<>();

    void register(String streamId, WebSocketSession session) {
        streams.computeIfAbsent(streamId, k -> ConcurrentHashMap.newKeySet()).add(session);
    }

    void unregister(String streamId, WebSocketSession session) {
        var set = streams.get(streamId);
        if (set != null) {
            set.remove(session);
            if (set.isEmpty())
                streams.remove(streamId);
        }
    }

    public void broadcast(String streamId, byte[] pcm16le) {
        var set = streams.get(streamId);
        if (set == null)
            return;
        BinaryMessage msg = new BinaryMessage(pcm16le);
        for (WebSocketSession s : set) {
            try {
                if (s.isOpen())
                    s.sendMessage(msg);
            } catch (Exception ignored) {
            }
        }
    }
}