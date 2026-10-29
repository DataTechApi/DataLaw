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

    public List<Object[]> obterQuantidadeProcessosPorOrgaoJulgador(String classeNome, String assuntoNome) {
        return processoRepository.findQuantidadeProcessosPorOrgaoJulgador(classeNome, assuntoNome);
    }

    public List<Object[]> obterQuantidadeProcessosPorClasse(String assuntoNome) {
        return processoRepository.findQuantidadeProcessosPorClasse(assuntoNome);
    }

    public Double obterTaxaSucessoPorClasse(String classeNome) {
        return processoRepository.findTaxaSucessoPorClasse(classeNome);
    }

    public List<Object[]> obterQuantidadeProcessosPorAssunto(String classeNome, String assuntoNome) {
        return processoRepository.findQuantidadeProcessosPorAssunto(classeNome, assuntoNome);
    }

    public Double obterTaxaSucessoPorAssunto(String assuntoNome) {
        return processoRepository.findTaxaSucessoPorAssunto(assuntoNome);
    }

    public List<Object[]> obterPrecedentesPorAssunto(String assuntoNome) {
        return processoRepository.findPrecedentesPorAssunto(assuntoNome);
    }
}
