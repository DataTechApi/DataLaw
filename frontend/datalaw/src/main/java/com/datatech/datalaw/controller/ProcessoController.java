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

    @GetMapping({"/", "/processos/orgaos-julgadores"})
    public String listarProcessosPorOrgao(@org.springframework.web.bind.annotation.RequestParam(value = "classeNome", required = false) String classeNome, Model model) {
        if (classeNome == null) {
            classeNome = "";
        }
        var processosPorOrgao = processoService.obterQuantidadeProcessosPorOrgaoJulgador(classeNome);
        var processosPorClasse = processoService.obterQuantidadeProcessosPorClasse();
        model.addAttribute("processos", processosPorOrgao);
        model.addAttribute("processosPorClasse", processosPorClasse);
        model.addAttribute("classeNome", classeNome);
        return "orgaos-julgadores";
    }

    @GetMapping("/processos/taxa-sucesso")
    @org.springframework.web.bind.annotation.ResponseBody
    public java.util.Map<String, Object> obterTaxaSucesso(@org.springframework.web.bind.annotation.RequestParam("classeNome") String classeNome) {
        Double taxa = processoService.obterTaxaSucessoPorClasse(classeNome);
        java.util.Map<String, Object> response = new java.util.HashMap<>();
        response.put("taxa", taxa);
        return response;
    }
}
