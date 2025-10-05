
package com.seistoseven.api;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.*;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {
    private final AudioWebSocketHandler audioWebSocketHandler;

    public WebSocketConfig(AudioWebSocketHandler audioWebSocketHandler) {
        this.audioWebSocketHandler = audioWebSocketHandler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry
                .addHandler(audioWebSocketHandler, "/audio/stream")
                .setAllowedOrigins("http://localhost:5173", "http://localhost:3000", "http://localhost:8080",
                        "http://127.0.0.1:*");
        // no SockJS: we need binary frames; keep it raw WS
    }
}