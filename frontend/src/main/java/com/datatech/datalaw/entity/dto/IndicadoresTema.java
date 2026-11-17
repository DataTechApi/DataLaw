package com.datatech.datalaw.entity.dto;

import java.util.List;

/**
 * Every Sprint 3 indicator shown for a selected topic.
 * {@code evidencias} is null when the topic has no curated thesis.
 */
public record IndicadoresTema(
        IndicadorAdesao adesao,
        ResultadoPorPolo polo,
        List<AdesaoPorGrupo> adesaoPorOrgao,
        List<AdesaoPorGrupo> adesaoPorTese,
        EvidenciasTese evidencias) {
}
