package com.seistoseven.api;

import org.json.JSONObject;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.multipart.MultipartFile;

@Controller
public class PythonController {

    public ResponseEntity<String> getRawAudio(
            @RequestParam("audio") MultipartFile audioFile,
            @RequestParam("fromLang") String fromLang,
            @RequestParam("toLang") String toLang) {
        // Logic to run the Python script and capture its outputpc

        JSONObject body = new JSONObject();
        body.put("payload", audioFile);
        body.put("to", toLang);
        body.put("from", fromLang);

        String pythonOutput = "Output from Python script"; // Replace with actual output

        return ResponseEntity.ok(pythonOutput);
    }
}
