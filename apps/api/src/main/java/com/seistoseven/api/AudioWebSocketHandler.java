package com.seistoseven.api;

import org.springframework.stereotype.Component;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.AbstractWebSocketHandler;

@Component
public class AudioWebSocketHandler extends AbstractWebSocketHandler {
    private final AudioBroadcaster broadcaster;

    public AudioWebSocketHandler(AudioBroadcaster broadcaster) {
        this.broadcaster = broadcaster;
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        String streamId = getStreamId(session);
        broadcaster.register(streamId, session);
    }

    @Override
    public void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String p = message.getPayload();
        if ("PING".equalsIgnoreCase(p)) {
            session.sendMessage(new TextMessage("PONG"));
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        String streamId = getStreamId(session);
        broadcaster.unregister(streamId, session);
    }

    private String getStreamId(WebSocketSession session) {
        var query = session.getUri() != null ? session.getUri().getQuery() : null;
        if (query != null) {
            for (String kv : query.split("&")) {
                String[] parts = kv.split("=", 2);
                if (parts.length == 2 && parts[0].equals("streamId"))
                    return parts[1];
            }
        }
        return "main";
    }
}