package com.datatech.datalaw.controller;

import com.datatech.datalaw.service.ProcessoService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.HashMap;
import java.util.Map;

@Controller
public class ProcessoController {

    private final ProcessoService processoService;

    public ProcessoController(ProcessoService processoService) {
        this.processoService = processoService;
    }

    @GetMapping({"/", "/processos/orgaos-julgadores"})
    public String listarProcessosPorOrgao(
            @RequestParam(value = "classeNome", required = false) String classeNome,
            @RequestParam(value = "assuntoNome", required = false) String assuntoNome,
            Model model) {
        if (classeNome == null) {
            classeNome = "";
        }
        if (assuntoNome == null) {
            assuntoNome = "";
        }
        var processosPorOrgao = processoService.obterQuantidadeProcessosPorOrgaoJulgador(classeNome, assuntoNome);
        var processosPorClasse = processoService.obterQuantidadeProcessosPorClasse(assuntoNome);
        var processosPorAssunto = processoService.obterQuantidadeProcessosPorAssunto(classeNome, assuntoNome);

        model.addAttribute("processos", processosPorOrgao);
        model.addAttribute("processosPorClasse", processosPorClasse);
        model.addAttribute("processosPorAssunto", processosPorAssunto);
        model.addAttribute("classeNome", classeNome);
        model.addAttribute("assuntoNome", assuntoNome);
        return "orgaos-julgadores";
    }

    @GetMapping("/processos/taxa-sucesso")
    @ResponseBody
    public Map<String, Object> obterTaxaSucesso(@RequestParam("classeNome") String classeNome) {
        Double taxa = processoService.obterTaxaSucessoPorClasse(classeNome);
        Map<String, Object> response = new HashMap<>();
        response.put("taxa", taxa);
        return response;
    }

    @GetMapping("/processos/taxa-sucesso-tema")
    @ResponseBody
    public Map<String, Object> obterTaxaSucessoTema(@RequestParam("assuntoNome") String assuntoNome) {
        Double taxa = processoService.obterTaxaSucessoPorAssunto(assuntoNome);
        var precedentes = processoService.obterPrecedentesPorAssunto(assuntoNome);
        Map<String, Object> response = new HashMap<>();
        response.put("taxa", taxa);
        response.put("precedentes", precedentes);
        return response;
    }
}
