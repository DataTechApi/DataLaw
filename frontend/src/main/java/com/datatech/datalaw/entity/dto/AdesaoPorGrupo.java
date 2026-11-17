package com.datatech.datalaw.entity.dto;

/**
 * Adherence Index of one group inside a topic: a judging body or a precedent.
 * {@code id} and {@code direcao} are filled only for precedents.
 */
public record AdesaoPorGrupo(
        String id,
        String nome,
        String detalhe,
        String direcao,
        Double indice,
        long decisoesComResultado,
        Confiabilidade confiabilidade) {
}
