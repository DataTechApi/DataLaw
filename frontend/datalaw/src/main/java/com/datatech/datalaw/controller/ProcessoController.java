package com.datatech.datalaw.controller;

import com.datatech.datalaw.service.ProcessoService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class ProcessoController {

    private final ProcessoService processoService;

    public ProcessoController(ProcessoService processoService) {
        this.processoService = processoService;
    }

    @GetMapping("/processos/orgaos-julgadores")
    public String listarProcessosPorOrgao(@org.springframework.web.bind.annotation.RequestParam(value = "classeNome", defaultValue = "Execução Fiscal") String classeNome, Model model) {
        var processosPorOrgao = processoService.obterQuantidadeProcessosPorOrgaoJulgador(classeNome);
        var processosPorClasse = processoService.obterQuantidadeProcessosPorClasse();
        model.addAttribute("processos", processosPorOrgao);
        model.addAttribute("processosPorClasse", processosPorClasse);
        model.addAttribute("classeNome", classeNome);
        return "orgaos-julgadores";
    }
}
