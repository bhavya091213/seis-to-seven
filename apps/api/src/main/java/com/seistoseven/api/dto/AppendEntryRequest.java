package com.seistoseven.api.dto;

public record AppendEntryRequest(
    double t,
    double dur,
    String speaker,
    String lang,
    String text
) {}
