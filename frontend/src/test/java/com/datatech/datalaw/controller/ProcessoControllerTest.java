package com.datatech.datalaw.controller;

import com.datatech.datalaw.service.ProcessoService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.hamcrest.Matchers.containsString;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.model;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;

@WebMvcTest(ProcessoController.class)
class ProcessoControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private ProcessoService processoService;

    @Test
    void raizSemFiltroUsaClasseVaziaERenderizaPagina() throws Exception {
        List<Object[]> porOrgao = List.<Object[]>of(new Object[]{"1ª Vara Cível", 10L});
        List<Object[]> porClasse = List.<Object[]>of(new Object[]{"Execução Fiscal", 7L});
        when(processoService.obterQuantidadeProcessosPorOrgaoJulgador("")).thenReturn(porOrgao);
        when(processoService.obterQuantidadeProcessosPorClasse()).thenReturn(porClasse);

        mockMvc.perform(get("/"))
                .andExpect(status().isOk())
                .andExpect(view().name("orgaos-julgadores"))
                .andExpect(model().attribute("classeNome", ""))
                .andExpect(model().attribute("processos", porOrgao))
                .andExpect(model().attribute("processosPorClasse", porClasse))
                .andExpect(content().string(containsString("Todos os processos")));

        verify(processoService).obterQuantidadeProcessosPorOrgaoJulgador("");
    }

    @Test
    void filtroPorClasseRepassaClasseAoServicoEMostraTitulo() throws Exception {
        when(processoService.obterQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal"))
                .thenReturn(List.<Object[]>of(new Object[]{"Vara de Execuções Fiscais", 3L}));
        when(processoService.obterQuantidadeProcessosPorClasse()).thenReturn(List.of());

        mockMvc.perform(get("/processos/orgaos-julgadores").param("classeNome", "Execução Fiscal"))
                .andExpect(status().isOk())
                .andExpect(view().name("orgaos-julgadores"))
                .andExpect(model().attribute("classeNome", "Execução Fiscal"))
                .andExpect(content().string(containsString("Vara de Execuções Fiscais")));

        verify(processoService).obterQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal");
    }

    @Test
    void paginaRenderizaSemDados() throws Exception {
        when(processoService.obterQuantidadeProcessosPorOrgaoJulgador(anyString())).thenReturn(List.of());
        when(processoService.obterQuantidadeProcessosPorClasse()).thenReturn(List.of());

        mockMvc.perform(get("/processos/orgaos-julgadores").param("classeNome", "Classe inexistente"))
                .andExpect(status().isOk())
                .andExpect(view().name("orgaos-julgadores"));
    }

    @Test
    void taxaSucessoRetornaJsonComTaxa() throws Exception {
        when(processoService.obterTaxaSucessoPorClasse("Procedimento Comum Cível")).thenReturn(62.5);

        mockMvc.perform(get("/processos/taxa-sucesso").param("classeNome", "Procedimento Comum Cível"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.taxa").value(62.5));
    }

    @Test
    void taxaSucessoSemClasseRetornaBadRequest() throws Exception {
        mockMvc.perform(get("/processos/taxa-sucesso"))
                .andExpect(status().isBadRequest());

        verify(processoService, never()).obterTaxaSucessoPorClasse(anyString());
    }
}
