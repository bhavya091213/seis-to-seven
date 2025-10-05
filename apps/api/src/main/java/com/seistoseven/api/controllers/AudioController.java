package com.seistoseven.api.controllers;

import com.seistoseven.api.bridge.PythonBridgeService;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletResponse;

import java.io.*;
import java.util.Base64;

@RestController
@RequestMapping("/api/voice")
@CrossOrigin // if your frontend is on another origin
public class AudioController {

    private final PythonBridgeService python;

    public AudioController(PythonBridgeService python) {
        this.python = python;
    }

    // Accept either file (Multipart) or base64; here’s the base64 variant for
    // simplicity
    @PostMapping(value = "/translate", consumes = MediaType.APPLICATION_JSON_VALUE)
    public void translate(@RequestBody TranslateRequest req, HttpServletResponse resp) throws IOException {
        // Validate
        if (req.from_lang == null || req.to_lang == null || req.audio_b64 == null) {
            resp.sendError(400, "from_lang, to_lang, audio_b64 required");
            return;
        }

        // Start python and stream its stdout to client
        var proc = python.startProcess(req.from_lang, req.to_lang, req.audio_b64);

        // We don’t know if TTS yields mp3 or wav—set a generic content type or your
        // known one.
        resp.setStatus(200);
        resp.setHeader(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=output.mp3");
        resp.setContentType("audio/mpeg"); // change to "audio/wav" if your TTS returns wav

        try (InputStream pyOut = proc.getInputStream();
                OutputStream out = resp.getOutputStream()) {

            pyOut.transferTo(out); // streams chunks as they arrive
            out.flush();
        } finally {
            // Ensure the process terminates
            try {
                int code = proc.waitFor();
                System.out.println("[python] exited with " + code);
            } catch (InterruptedException ignored) {
                proc.destroyForcibly();
            }
        }
    }

    public static class TranslateRequest {
        public String from_lang;
        public String to_lang;
        public String audio_b64;
    }
}
