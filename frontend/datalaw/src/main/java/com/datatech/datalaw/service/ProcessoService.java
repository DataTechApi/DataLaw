package com.datatech.datalaw.service;

import com.datatech.datalaw.repository.ProcessoRepository;

public class ProcessoService {

    private final ProcessoRepository processoRepository;

    public ProcessoService(ProcessoRepository processoRepository) {
        this.processoRepository = processoRepository;
    }

    public void exibirQuantidadeProcessosPorOrgaoJulgador() {
        var resultados = processoRepository.findQuantidadeProcessosPorOrgaoJulgador();
        for (Object[] resultado : resultados) {
            String orgaoJulgador = (String) resultado[0];
            Long quantidade = (Long) resultado[1];
            System.out.println("Órgão Julgador: " + orgaoJulgador + ", Quantidade de Processos: " + quantidade);
        }
    }
}
