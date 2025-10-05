package com.seistoseven.api.bridge;

import org.springframework.stereotype.Service;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

@Service
public class PythonBridgeService {

    private String resolvePythonBinary() {
        // Project root
        String root = System.getProperty("user.dir"); // repo root when running from IDE
        // Your venv is `../../../venv` relative to the module; normalize from root:
        // Make this tolerant: if not found, fall back to system "python"
        Path venvBin = isWindows()
                ? Paths.get(root, "venv", "Scripts", "python.exe")
                : Paths.get(root, "venv", "bin", "python");

        if (venvBin.toFile().exists())
            return venvBin.toAbsolutePath().toString();
        // Try ../../../venv for monorepo app placement
        Path monorepoVenv = isWindows()
                ? Paths.get(root, "..", "..", "..", "venv", "Scripts", "python.exe")
                : Paths.get(root, "..", "..", "..", "venv", "bin", "python");
        if (monorepoVenv.toFile().exists())
            return monorepoVenv.toAbsolutePath().toString();

        return "python"; // last resort
    }

    private boolean isWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }

    private File resolvePythonWorkingDir() {
        // We want PY files under src/main/python and main at apps/main.py
        return Paths.get(System.getProperty("user.dir"), "src", "main", "python").toFile();
    }

    private File resolveMainPy() {
        return Paths.get(resolvePythonWorkingDir().getPath(), "apps", "main.py").toFile();
    }

    /**
     * Launches Python, sends JSON on stdin, and returns a streaming InputStream of
     * stdout.
     * The caller must consume and close the stream.
     */
    public Process startProcess(String fromLang, String toLang, String audioB64) throws IOException {
        String python = resolvePythonBinary();
        File workDir = resolvePythonWorkingDir();
        File mainPy = resolveMainPy();

        if (!mainPy.exists()) {
            throw new FileNotFoundException("Python entry not found at: " + mainPy.getAbsolutePath());
        }

        List<String> cmd = new ArrayList<>();
        cmd.add(python);
        cmd.add(mainPy.getAbsolutePath());

        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.directory(workDir);

        // Ensure imports like `from apps...` work
        Map<String, String> env = pb.environment();
        String pyPath = workDir.getAbsolutePath();
        env.put("PYTHONPATH", pyPath);

        // Useful for debugging
        env.put("PYTHONUNBUFFERED", "1");

        Process process = pb.start();

        // Send JSON to stdin
        String json = String.format(Locale.ROOT,
                "{\"from_lang\":\"%s\",\"to_lang\":\"%s\",\"audio_b64\":\"%s\"}",
                escape(fromLang), escape(toLang), escape(audioB64));

        try (OutputStream stdin = process.getOutputStream()) {
            stdin.write(json.getBytes(StandardCharsets.UTF_8));
            stdin.flush();
        }

        // Optionally read and log stderr on a background thread
        new Thread(() -> {
            try (BufferedReader br = new BufferedReader(
                    new InputStreamReader(process.getErrorStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = br.readLine()) != null) {
                    System.err.println("[py STDERR] " + line);
                }
            } catch (IOException ignored) {
            }
        }, "python-stderr-drain").start();

        return process;
    }

    private static String escape(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
