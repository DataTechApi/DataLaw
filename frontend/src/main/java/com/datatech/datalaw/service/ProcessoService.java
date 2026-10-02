package com.datatech.datalaw.service;

import com.datatech.datalaw.repository.ProcessoRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ProcessoService {

    private final ProcessoRepository processoRepository;

    public ProcessoService(ProcessoRepository processoRepository) {
        this.processoRepository = processoRepository;
    }

    public List<Object[]> obterQuantidadeProcessosPorOrgaoJulgador(String classeNome) {
        return processoRepository.findQuantidadeProcessosPorOrgaoJulgador(classeNome);
    }

    public List<Object[]> obterQuantidadeProcessosPorClasse() {
        return processoRepository.findQuantidadeProcessosPorClasse();
    }

    public Double obterTaxaSucessoPorClasse(String classeNome) {
        return processoRepository.findTaxaSucessoPorClasse(classeNome);
    }
}
