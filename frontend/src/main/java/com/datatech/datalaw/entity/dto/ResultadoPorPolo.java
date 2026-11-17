package com.datatech.datalaw.entity.dto;

import java.time.OffsetDateTime;

/**
 * Split of merit results between plaintiff and defendant in a topic.
 * Percentages are null when the topic has no decisions with a result.
 */
public record ResultadoPorPolo(
        Double autorPct,
        Double reuPct,
        long procedentes,
        long parciais,
        long improcedentes,
        long decisoesComResultado,
        long processosEncerrados,
        Confiabilidade confiabilidade,
        OffsetDateTime atualizadoEm) {
}
