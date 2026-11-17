package com.datatech.datalaw.entity.dto;

import java.time.OffsetDateTime;

/**
 * Adherence Index of the main curated thesis of a topic: the one with the largest sample.
 * Theses with opposite directions are never summed, because their indexes would cancel out.
 * {@code indice} and {@code cobertura} are null when there is no data to calculate them,
 * and {@code tese} is null when the topic has no thesis with a recorded direction.
 */
public record IndicadorAdesao(
        String tese,
        String tribunalTese,
        String direcao,
        Double indice,
        long aderentes,
        long parciais,
        long naoAderentes,
        long decisoesComResultado,
        long processosEncerrados,
        Double cobertura,
        Confiabilidade confiabilidade,
        OffsetDateTime atualizadoEm) {

    public static IndicadorAdesao semTeseCurada() {
        return new IndicadorAdesao(null, null, null, null, 0, 0, 0, 0, 0, null,
                Confiabilidade.INSUFICIENTE, null);
    }

    public boolean possuiTeseCurada() {
        return tese != null;
    }
}
