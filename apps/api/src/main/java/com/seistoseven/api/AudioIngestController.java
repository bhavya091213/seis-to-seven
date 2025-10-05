package com.seistoseven.api;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/audio")
public class AudioIngestController {
    private final AudioBroadcaster broadcaster;

    public AudioIngestController(AudioBroadcaster broadcaster) {
        this.broadcaster = broadcaster;
    }

    // POST raw body: application/octet-stream
    @PostMapping(value = "/push/{streamId}", consumes = MediaType.APPLICATION_OCTET_STREAM_VALUE)
    public String pushRaw(@PathVariable String streamId, @RequestBody byte[] data) {
        broadcaster.broadcast(streamId, data);
        return "ok";
    }

    // POST file: multipart/form-data
    @PostMapping(value = "/push-file/{streamId}", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public String pushFile(@PathVariable String streamId, @RequestParam("file") MultipartFile file) throws Exception {
        broadcaster.broadcast(streamId, file.getBytes());
        return "ok";
    }
}