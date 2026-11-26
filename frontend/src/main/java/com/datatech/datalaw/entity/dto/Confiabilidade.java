package com.datatech.datalaw.entity.dto;

/**
 * Reliability of an indicator, based on the number of decisions with a merit result.
 */
public enum Confiabilidade {

    INSUFICIENTE("Dados insuficientes"),
    BAIXA("Baixa"),
    ADEQUADA("Adequada");

    public static final long AMOSTRA_MINIMA = 30;

    private final String rotulo;

    Confiabilidade(String rotulo) {
        this.rotulo = rotulo;
    }

    public String getRotulo() {
        return rotulo;
    }

    public static Confiabilidade paraAmostra(long decisoesComResultado) {
        if (decisoesComResultado <= 0) {
            return INSUFICIENTE;
        }
        return decisoesComResultado < AMOSTRA_MINIMA ? BAIXA : ADEQUADA;
    }
}
