package com.datatech.datalaw.controller;

import com.datatech.datalaw.entity.dto.AdesaoPorGrupo;
import com.datatech.datalaw.entity.dto.Confiabilidade;
import com.datatech.datalaw.entity.dto.EvidenciaDecisao;
import com.datatech.datalaw.entity.dto.EvidenciasTese;
import com.datatech.datalaw.entity.dto.IndicadorAdesao;
import com.datatech.datalaw.entity.dto.IndicadoresTema;
import com.datatech.datalaw.entity.dto.ResultadoPorPolo;
import com.datatech.datalaw.service.ProcessoService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.not;
import static org.hamcrest.Matchers.nullValue;
import static org.mockito.ArgumentMatchers.any;
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
        List<Object[]> porAssunto = List.<Object[]>of(new Object[]{"Dano Moral", 35L});
        when(processoService.obterQuantidadeProcessosPorOrgaoJulgador("", "")).thenReturn(porOrgao);
        when(processoService.obterQuantidadeProcessosPorClasse("")).thenReturn(porClasse);
        when(processoService.obterQuantidadeProcessosPorAssunto("", "")).thenReturn(porAssunto);

        mockMvc.perform(get("/"))
                .andExpect(status().isOk())
                .andExpect(view().name("orgaos-julgadores"))
                .andExpect(model().attribute("classeNome", ""))
                .andExpect(model().attribute("assuntoNome", ""))
                .andExpect(model().attribute("processos", porOrgao))
                .andExpect(model().attribute("processosPorClasse", porClasse))
                .andExpect(model().attribute("processosPorAssunto", porAssunto))
                .andExpect(content().string(containsString("Visão Geral dos Processos")));

        verify(processoService).obterQuantidadeProcessosPorOrgaoJulgador("", "");
    }

    @Test
    void filtroPorClasseRepassaClasseAoServicoEMostraTitulo() throws Exception {
        when(processoService.obterQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal", ""))
                .thenReturn(List.<Object[]>of(new Object[]{"Vara de Execuções Fiscais", 3L}));
        when(processoService.obterQuantidadeProcessosPorClasse("")).thenReturn(List.of());
        when(processoService.obterQuantidadeProcessosPorAssunto("Execução Fiscal", "")).thenReturn(List.of());

        mockMvc.perform(get("/processos/orgaos-julgadores").param("classeNome", "Execução Fiscal"))
                .andExpect(status().isOk())
                .andExpect(view().name("orgaos-julgadores"))
                .andExpect(model().attribute("classeNome", "Execução Fiscal"))
                .andExpect(content().string(containsString("Vara de Execuções Fiscais")));

        verify(processoService).obterQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal", "");
    }

    @Test
    void paginaRenderizaSemDados() throws Exception {
        when(processoService.obterQuantidadeProcessosPorOrgaoJulgador(anyString(), anyString())).thenReturn(List.of());
        when(processoService.obterQuantidadeProcessosPorClasse(anyString())).thenReturn(List.of());
        when(processoService.obterQuantidadeProcessosPorAssunto(anyString(), anyString())).thenReturn(List.of());

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

    @Test
    void filtroPorTemaEClasseRepassaAmbosAoServicoEMostraTitulo() throws Exception {
        when(processoService.obterQuantidadeProcessosPorOrgaoJulgador("Procedimento Comum Cível", "Dano Moral"))
                .thenReturn(List.<Object[]>of(new Object[]{"2ª Vara Cível", 35L}));
        when(processoService.obterQuantidadeProcessosPorClasse("Dano Moral"))
                .thenReturn(List.<Object[]>of(new Object[]{"Procedimento Comum Cível", 35L}));
        when(processoService.obterQuantidadeProcessosPorAssunto("Procedimento Comum Cível", "Dano Moral"))
                .thenReturn(List.<Object[]>of(new Object[]{"Dano Moral", 35L}));

        mockMvc.perform(get("/processos/orgaos-julgadores")
                        .param("assuntoNome", "Dano Moral")
                        .param("classeNome", "Procedimento Comum Cível"))
                .andExpect(status().isOk())
                .andExpect(model().attribute("assuntoNome", "Dano Moral"))
                .andExpect(content().string(containsString("Tema: Dano Moral · Classe: Procedimento Comum Cível")));

        verify(processoService).obterQuantidadeProcessosPorOrgaoJulgador("Procedimento Comum Cível", "Dano Moral");
        verify(processoService).obterQuantidadeProcessosPorClasse("Dano Moral");
        verify(processoService).obterQuantidadeProcessosPorAssunto("Procedimento Comum Cível", "Dano Moral");
    }

    @Test
    void taxaSucessoTemaRetornaJsonComTaxaEPrecedentes() throws Exception {
        when(processoService.obterTaxaSucessoPorAssunto("Dano Moral")).thenReturn(48.25);
        when(processoService.obterPrecedentesPorAssunto("Dano Moral"))
                .thenReturn(List.<Object[]>of(new Object[]{"Tema 1234", "STJ"}));

        mockMvc.perform(get("/processos/taxa-sucesso-tema").param("assuntoNome", "Dano Moral"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.taxa").value(48.25))
                .andExpect(jsonPath("$.precedentes[0][0]").value("Tema 1234"))
                .andExpect(jsonPath("$.precedentes[0][1]").value("STJ"));
    }

    @Test
    void taxaSucessoTemaSemAssuntoRetornaBadRequest() throws Exception {
        mockMvc.perform(get("/processos/taxa-sucesso-tema"))
                .andExpect(status().isBadRequest());

        verify(processoService, never()).obterTaxaSucessoPorAssunto(anyString());
        verify(processoService, never()).obterPrecedentesPorAssunto(anyString());
    }

    private static IndicadoresTema indicadoresComDados() {
        return new IndicadoresTema(
                new IndicadorAdesao("Tema Repetitivo 1234", "STJ", "autor", 70.0, 6, 2, 2, 10, 20, 50.0,
                        Confiabilidade.BAIXA, OffsetDateTime.parse("2026-11-13T10:00:00Z")),
                new ResultadoPorPolo(70.0, 30.0, 60, 20, 20, 100, 120, Confiabilidade.ADEQUADA,
                        OffsetDateTime.parse("2026-11-13T10:00:00Z")),
                List.of(new AdesaoPorGrupo(null, "2ª Vara Cível", null, null, 80.0, 5, Confiabilidade.BAIXA)),
                List.of(new AdesaoPorGrupo("tese-1", "Tema Repetitivo 1234", "STJ", "autor", 70.0, 10,
                        Confiabilidade.BAIXA)),
                new EvidenciasTese("tese-1", "Tema Repetitivo 1234", "STJ", "autor",
                        List.of(new EvidenciaDecisao("0004584-44.2021.8.26.0562", "2ª Vara Cível", "Procedência",
                                LocalDate.of(2026, 6, 1), EvidenciaDecisao.Classificacao.ADERENTE)),
                        10, 6, 2, 2, true, 50));
    }

    private static IndicadoresTema indicadoresSemDados() {
        return new IndicadoresTema(
                IndicadorAdesao.semTeseCurada(),
                new ResultadoPorPolo(null, null, 0, 0, 0, 0, 3, Confiabilidade.INSUFICIENTE, null),
                List.of(),
                List.of(),
                null);
    }

    private void semGraficosDeVolume() {
        when(processoService.obterQuantidadeProcessosPorOrgaoJulgador(anyString(), anyString())).thenReturn(List.of());
        when(processoService.obterQuantidadeProcessosPorClasse(anyString())).thenReturn(List.of());
        when(processoService.obterQuantidadeProcessosPorAssunto(anyString(), anyString())).thenReturn(List.of());
    }

    @Test
    void temaSelecionadoMostraAdesaoPoloOrgaosETeses() throws Exception {
        semGraficosDeVolume();
        when(processoService.obterIndicadoresTema("Dano Moral", null)).thenReturn(indicadoresComDados());

        mockMvc.perform(get("/processos/orgaos-julgadores").param("assuntoNome", " Dano Moral "))
                .andExpect(status().isOk())
                .andExpect(model().attributeExists("indicadores"))
                .andExpect(content().string(containsString("Índice de Adesão à Tese")))
                .andExpect(content().string(containsString("Tese principal (maior amostra):")))
                .andExpect(content().string(containsString("70,0%")))
                .andExpect(content().string(containsString("30,0%")))
                .andExpect(content().string(containsString("Resultados por Polo")))
                .andExpect(content().string(containsString("2ª Vara Cível")))
                .andExpect(content().string(containsString("Tema Repetitivo 1234")))
                .andExpect(content().string(containsString("favorece o autor")))
                .andExpect(content().string(containsString("13/11/2026")))
                .andExpect(content().string(containsString("Evidências do Índice")))
                .andExpect(content().string(containsString("0004584-44.2021.8.26.0562")))
                .andExpect(content().string(containsString("01/06/2026")))
                .andExpect(content().string(containsString("Totais conferem com o índice")))
                .andExpect(content().string(containsString("teseId=tese-1")));

        verify(processoService).obterIndicadoresTema("Dano Moral", null);
    }

    @Test
    void temaSemDadosMostraDadosInsuficientesENuncaZero() throws Exception {
        semGraficosDeVolume();
        when(processoService.obterIndicadoresTema("Tema vazio", null)).thenReturn(indicadoresSemDados());

        mockMvc.perform(get("/processos/orgaos-julgadores").param("assuntoNome", "Tema vazio"))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("Dados insuficientes")))
                .andExpect(content().string(containsString("Nenhuma tese com direção registrada para este tema.")))
                .andExpect(content().string(containsString("não há decisões avaliadas")))
                .andExpect(content().string(not(containsString("0,0%"))));
    }

    @Test
    void semTemaNaoCalculaIndicadores() throws Exception {
        semGraficosDeVolume();

        mockMvc.perform(get("/processos/orgaos-julgadores").param("classeNome", "Execução Fiscal"))
                .andExpect(status().isOk())
                .andExpect(model().attributeDoesNotExist("indicadores"))
                .andExpect(content().string(not(containsString("Índice de Adesão à Tese"))));

        verify(processoService, never()).obterIndicadoresTema(anyString(), any());
    }

    @Test
    void indicadoresTemaRetornaJson() throws Exception {
        when(processoService.obterIndicadoresTema("Dano Moral", null)).thenReturn(indicadoresComDados());

        mockMvc.perform(get("/processos/indicadores-tema").param("assuntoNome", "Dano Moral"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.adesao.indice").value(70.0))
                .andExpect(jsonPath("$.polo.autorPct").value(70.0))
                .andExpect(jsonPath("$.polo.reuPct").value(30.0))
                .andExpect(jsonPath("$.adesaoPorOrgao[0].nome").value("2ª Vara Cível"))
                .andExpect(jsonPath("$.evidencias.total").value(10))
                .andExpect(jsonPath("$.evidencias.decisoes[0].classificacao").value("ADERENTE"));
    }

    @Test
    void indicadoresTemaSemAssuntoRetornaBadRequest() throws Exception {
        mockMvc.perform(get("/processos/indicadores-tema"))
                .andExpect(status().isBadRequest());

        verify(processoService, never()).obterIndicadoresTema(anyString(), any());
    }

    @Test
    void taxaSucessoSemDadosRetornaNuloENaoZero() throws Exception {
        when(processoService.obterTaxaSucessoPorAssunto("Tema vazio")).thenReturn(null);
        when(processoService.obterPrecedentesPorAssunto("Tema vazio")).thenReturn(List.of());

        mockMvc.perform(get("/processos/taxa-sucesso-tema").param("assuntoNome", "Tema vazio"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.taxa").value(nullValue()));
    }

    @Test
    void teseSelecionadaERepassadaParaAsEvidencias() throws Exception {
        semGraficosDeVolume();
        when(processoService.obterIndicadoresTema("Dano Moral", "tese-1")).thenReturn(indicadoresComDados());

        mockMvc.perform(get("/processos/orgaos-julgadores")
                        .param("assuntoNome", "Dano Moral")
                        .param("teseId", "tese-1"))
                .andExpect(status().isOk())
                .andExpect(model().attribute("teseId", "tese-1"))
                .andExpect(content().string(containsString("data-initial-section=\"evidence\"")))
                .andExpect(content().string(containsString("Evidências do Índice")));

        verify(processoService).obterIndicadoresTema("Dano Moral", "tese-1");
    }

    @Test
    void exploradorPreservaClasseAoSelecionarTemaETese() throws Exception {
        when(processoService.obterQuantidadeProcessosPorOrgaoJulgador("Classe", "Dano Moral"))
                .thenReturn(List.of());
        when(processoService.obterQuantidadeProcessosPorClasse("Dano Moral"))
                .thenReturn(List.of());
        when(processoService.obterQuantidadeProcessosPorAssunto("Classe", "Dano Moral"))
                .thenReturn(List.<Object[]>of(new Object[]{"Dano Moral", 35L}));
        when(processoService.obterIndicadoresTema("Dano Moral", null))
                .thenReturn(indicadoresComDados());

        mockMvc.perform(get("/processos/orgaos-julgadores")
                        .param("assuntoNome", "Dano Moral")
                        .param("classeNome", "Classe"))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("assuntoNome=Dano%20Moral&amp;classeNome=Classe")))
                .andExpect(content().string(containsString("classeNome=Classe&amp;temaSelecionado=Dano%20Moral&amp;teseId=tese-1#evidencias")))
                .andExpect(content().string(containsString("Não confirma a aplicação do precedente no texto da decisão.")));
    }

    @Test
    void exploradorDisponibilizaNomesContagensETaxasSemGraficos() throws Exception {
        when(processoService.obterQuantidadeProcessosPorOrgaoJulgador("", ""))
                .thenReturn(List.<Object[]>of(new Object[]{"Vara Cível", 45L}));
        when(processoService.obterQuantidadeProcessosPorClasse(""))
                .thenReturn(List.<Object[]>of(new Object[]{"Execução Fiscal", 35L}));
        when(processoService.obterQuantidadeProcessosPorAssunto("", ""))
                .thenReturn(List.<Object[]>of(new Object[]{"Dano Moral", 40L}));

        mockMvc.perform(get("/processos/orgaos-julgadores"))
                .andExpect(status().isOk())
                .andExpect(content().string(containsString("data-name=\"Execução Fiscal\"")))
                .andExpect(content().string(containsString("data-count=\"35\"")))
                .andExpect(content().string(containsString("data-kind=\"classe\"")))
                .andExpect(content().string(containsString("data-kind=\"orgao\"")))
                .andExpect(content().string(containsString("Dano Moral")))
                .andExpect(content().string(containsString("Selecione um tema para analisar.")))
                .andExpect(content().string(not(containsString("<canvas"))));
    }

    @Test
    void selecionarTemaNaoRestringeAListaDoAcervo() throws Exception {
        semGraficosDeVolume();
        when(processoService.obterQuantidadeProcessosPorAssunto("", ""))
                .thenReturn(List.<Object[]>of(new Object[]{"Dano Moral", 40L}, new Object[]{"IPTU", 60L}));
        when(processoService.obterIndicadoresTema("Dano Moral", null))
                .thenReturn(indicadoresComDados());

        mockMvc.perform(get("/processos/orgaos-julgadores").param("temaSelecionado", "Dano Moral"))
                .andExpect(status().isOk())
                .andExpect(model().attribute("assuntoNome", ""))
                .andExpect(model().attribute("temaSelecionado", "Dano Moral"))
                .andExpect(content().string(containsString("IPTU")))
                .andExpect(content().string(containsString("Ver todos os temas")))
                .andExpect(content().string(containsString("Voltar ao acervo")))
                .andExpect(content().string(containsString("temaSelecionado=IPTU")));

        verify(processoService).obterQuantidadeProcessosPorAssunto("", "");
        verify(processoService).obterIndicadoresTema("Dano Moral", null);
    }

    @Test
    void buscaDoAcervoESelecaoDoTemaSaoIndependentes() throws Exception {
        when(processoService.obterQuantidadeProcessosPorOrgaoJulgador("", "Dano")).thenReturn(List.of());
        when(processoService.obterQuantidadeProcessosPorClasse("Dano")).thenReturn(List.of());
        when(processoService.obterQuantidadeProcessosPorAssunto("", "Dano")).thenReturn(List.of());
        when(processoService.obterIndicadoresTema("Dano Moral", null)).thenReturn(indicadoresComDados());

        mockMvc.perform(get("/processos/orgaos-julgadores")
                        .param("assuntoNome", "Dano").param("temaSelecionado", "Dano Moral"))
                .andExpect(status().isOk())
                .andExpect(model().attribute("assuntoNome", "Dano"))
                .andExpect(model().attribute("temaSelecionado", "Dano Moral"));

        verify(processoService).obterQuantidadeProcessosPorAssunto("", "Dano");
        verify(processoService).obterIndicadoresTema("Dano Moral", null);
        verify(processoService, never()).obterIndicadoresTema("Dano", null);
    }
}
