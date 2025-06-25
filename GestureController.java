package com.ai.gesture.controller;

import org.springframework.web.bind.annotation.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api/gesture")
public class GestureController {

    static class GestureData {
        public String word;
        public LocalDateTime timestamp;
    }

    private final List<GestureData> gestureList = new ArrayList<>();

    @PostMapping
    public String receiveGesture(@RequestBody GestureData data) {
        gestureList.add(0, data); // Add to top
        if (gestureList.size() > 10) {
            gestureList.remove(gestureList.size() - 1); // Keep only 10 recent
        }
        System.out.println("Received: " + data.word + " at " + data.timestamp);
        return "Received: " + data.word;
    }

    @GetMapping
    public List<GestureData> getRecentGestures() {
        return gestureList;
    }
}
