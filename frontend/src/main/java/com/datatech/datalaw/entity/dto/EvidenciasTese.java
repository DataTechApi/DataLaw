package com.datatech.datalaw.entity.dto;

import java.util.List;

/**
 * Decisions behind the Adherence Index of one thesis.
 * {@code decisoes} holds the most recent ones (at most {@code limite});
 * the totals cover every decision, and {@code conferemComIndice} tells whether
 * they match the counts used by the index.
 */
public record EvidenciasTese(
        String teseId,
        String tese,
        String tribunalTese,
        String direcao,
        List<EvidenciaDecisao> decisoes,
        long total,
        long aderentes,
        long parciais,
        long naoAderentes,
        boolean conferemComIndice,
        int limite) {

    public boolean listaParcial() {
        return total > decisoes.size();
    }
}
