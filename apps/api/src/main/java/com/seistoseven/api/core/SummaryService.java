package com.seistoseven.api.core;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.seistoseven.api.dto.TranscriptEntry;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class SummaryService {
    private final ObjectMapper mapper = new ObjectMapper();

    // Command to run your summarizer CLI
    private static final String PYTHON = "python"; // or an absolute path to your venv's python
    private static final String[] CMD = { PYTHON, "-m", "apps.gemini_api.summarize_cli" };

    /**
     * Calls the Python summarizer (stdin -> stdout).
     * Working dir is set to src/main/python so "apps.gemini_api" resolves.
     */
    public String summarize(List<TranscriptEntry> entries, String targetLang) throws Exception {
        ProcessBuilder pb = new ProcessBuilder(CMD);
        // Set working directory so Python finds the 'apps' package
        pb.directory(new File("src/main/python"));
        // Inherit stderr so Python errors show up in your Java logs
        pb.redirectError(ProcessBuilder.Redirect.INHERIT);

        Process p = pb.start();

        Map<String, Object> payload = new HashMap<>();
        payload.put("entries", entries);
        payload.put("target_lang", targetLang);

        try (OutputStream stdin = p.getOutputStream()) {
            stdin.write(mapper.writeValueAsBytes(payload));
            stdin.flush();
        }

        String out = new String(p.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
        int code = p.waitFor();

        Map<?, ?> resp = mapper.readValue(out, Map.class);
        if (code == 0 && "ok".equals(resp.get("status"))) {
            return String.valueOf(resp.get("summary_text"));
        }
        throw new RuntimeException("Summarizer failed: " + resp.get("message"));
    }
}
