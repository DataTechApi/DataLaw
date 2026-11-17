package com.datatech.datalaw.entity.dto;

import java.time.LocalDate;

/**
 * One decision used in the Adherence Index of a thesis. Holds no party data.
 */
public record EvidenciaDecisao(
        String numeroProcesso,
        String orgaoJulgador,
        String movimento,
        LocalDate dataJulgamento,
        Classificacao classificacao) {

    public enum Classificacao {

        ADERENTE("Aderente"),
        PARCIAL("Parcialmente aderente"),
        NAO_ADERENTE("Não aderente");

        private final String rotulo;

        Classificacao(String rotulo) {
            this.rotulo = rotulo;
        }

        public String getRotulo() {
            return rotulo;
        }

        public static Classificacao deGold(String valor) {
            return switch (valor) {
                case "aderente" -> ADERENTE;
                case "parcial" -> PARCIAL;
                default -> NAO_ADERENTE;
            };
        }
    }
}
