package com.datatech.datalaw.service;

import com.datatech.datalaw.entity.dto.AdesaoPorGrupo;
import com.datatech.datalaw.entity.dto.Confiabilidade;
import com.datatech.datalaw.entity.dto.EvidenciaDecisao;
import com.datatech.datalaw.entity.dto.EvidenciasTese;
import com.datatech.datalaw.entity.dto.IndicadorAdesao;
import com.datatech.datalaw.entity.dto.ResultadoPorPolo;
import com.datatech.datalaw.repository.ProcessoRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ProcessoServiceTest {

    @Mock
    private ProcessoRepository processoRepository;

    @InjectMocks
    private ProcessoService processoService;

    @Test
    void quantidadePorOrgaoJulgadorRepassaFiltroDeClasseEAssunto() {
        List<Object[]> esperado = List.<Object[]>of(new Object[]{"1ª Vara Cível", 10L});
        when(processoRepository.findQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal", "IPTU")).thenReturn(esperado);

        assertThat(processoService.obterQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal", "IPTU")).isSameAs(esperado);
        verify(processoRepository).findQuantidadeProcessosPorOrgaoJulgador("Execução Fiscal", "IPTU");
    }

    @Test
    void quantidadePorClasseRetornaResultadoDoRepositorio() {
        List<Object[]> esperado = List.<Object[]>of(new Object[]{"Execução Fiscal", 7L});
        when(processoRepository.findQuantidadeProcessosPorClasse("IPTU")).thenReturn(esperado);

        assertThat(processoService.obterQuantidadeProcessosPorClasse("IPTU")).isSameAs(esperado);
        verify(processoRepository).findQuantidadeProcessosPorClasse("IPTU");
    }

    @Test
    void quantidadePorAssuntoRetornaResultadoDoRepositorio() {
        List<Object[]> esperado = List.<Object[]>of(new Object[]{"Dano Moral", 15L});
        when(processoRepository.findQuantidadeProcessosPorAssunto("Procedimento Comum Cível", "Dano")).thenReturn(esperado);

        assertThat(processoService.obterQuantidadeProcessosPorAssunto("Procedimento Comum Cível", "Dano")).isSameAs(esperado);
        verify(processoRepository).findQuantidadeProcessosPorAssunto("Procedimento Comum Cível", "Dano");
    }

    @Test
    void taxaSucessoPorClasseRetornaValorDoRepositorio() {
        when(processoRepository.findTaxaSucessoPorClasse("Procedimento Comum Cível")).thenReturn(62.5);

        assertThat(processoService.obterTaxaSucessoPorClasse("Procedimento Comum Cível")).isEqualTo(62.5);
    }

    @Test
    void taxaSucessoPorAssuntoRetornaValorDoRepositorio() {
        when(processoRepository.findTaxaSucessoPorAssunto("Dano Moral")).thenReturn(48.25);

        assertThat(processoService.obterTaxaSucessoPorAssunto("Dano Moral")).isEqualTo(48.25);
    }

    @Test
    void precedentesPorAssuntoRetornaResultadoDoRepositorio() {
        List<Object[]> esperado = List.<Object[]>of(new Object[]{"Tema 1234", "STJ"});
        when(processoRepository.findPrecedentesPorAssunto("Dano Moral")).thenReturn(esperado);

        assertThat(processoService.obterPrecedentesPorAssunto("Dano Moral")).isSameAs(esperado);
        verify(processoRepository).findPrecedentesPorAssunto("Dano Moral");
    }

    @Test
    void percentualPonderaParciaisPelaMetade() {
        assertThat(ProcessoService.percentual(6, 2, 10)).isEqualTo(70.0);
        assertThat(ProcessoService.percentual(2, 2, 10)).isEqualTo(30.0);
        assertThat(ProcessoService.percentual(1, 0, 3)).isEqualTo(33.33);
    }

    @Test
    void percentualSemDecisoesEhNuloENaoZero() {
        assertThat(ProcessoService.percentual(0, 0, 0)).isNull();
        assertThat(ProcessoService.cobertura(0, 0)).isNull();
    }

    @Test
    void confiabilidadeDependeDaAmostraMinima() {
        assertThat(Confiabilidade.paraAmostra(0)).isEqualTo(Confiabilidade.INSUFICIENTE);
        assertThat(Confiabilidade.paraAmostra(29)).isEqualTo(Confiabilidade.BAIXA);
        assertThat(Confiabilidade.paraAmostra(30)).isEqualTo(Confiabilidade.ADEQUADA);
    }

    @Test
    void resultadoPorPoloDivideProcedenciaEImprocedencia() {
        OffsetDateTime atualizado = OffsetDateTime.of(2026, 11, 13, 10, 0, 0, 0, ZoneOffset.UTC);
        when(processoRepository.findTotaisPorPolo("Dano Moral"))
                .thenReturn(List.<Object[]>of(new Object[]{60L, 20L, 20L, 100L, 120L, atualizado}));

        ResultadoPorPolo polo = processoService.obterResultadoPorPolo("Dano Moral");

        assertThat(polo.autorPct()).isEqualTo(70.0);
        assertThat(polo.reuPct()).isEqualTo(30.0);
        assertThat(polo.decisoesComResultado()).isEqualTo(100);
        assertThat(polo.confiabilidade()).isEqualTo(Confiabilidade.ADEQUADA);
        assertThat(polo.atualizadoEm()).isAtSameInstantAs(atualizado);
        assertThat(polo.atualizadoEm().getOffset()).isEqualTo(ZoneOffset.ofHours(-3));
    }

    @Test
    void resultadoPorPoloSemDecisoesMostraDadosInsuficientes() {
        when(processoRepository.findTotaisPorPolo("Tema vazio"))
                .thenReturn(List.<Object[]>of(new Object[]{0L, 0L, 0L, 0L, 4L, null}));

        ResultadoPorPolo polo = processoService.obterResultadoPorPolo("Tema vazio");

        assertThat(polo.autorPct()).isNull();
        assertThat(polo.reuPct()).isNull();
        assertThat(polo.confiabilidade()).isEqualTo(Confiabilidade.INSUFICIENTE);
    }

    private static Object[] tese(String id, String identificador, String direcao,
                                 long aderentes, long parciais, long decisoes, long naoAderentes,
                                 long encerrados, Object atualizado) {
        return new Object[]{id, identificador, "STJ", "Título " + identificador, direcao,
                BigDecimal.valueOf(aderentes), BigDecimal.valueOf(parciais), BigDecimal.valueOf(decisoes),
                BigDecimal.valueOf(naoAderentes), BigDecimal.valueOf(encerrados), atualizado};
    }

    @Test
    void indicadorAdesaoCalculaIndiceCoberturaEConfiabilidade() {
        Timestamp atualizado = Timestamp.from(Instant.parse("2026-11-13T10:00:00Z"));
        when(processoRepository.findAdesaoPorTese("Dano Moral")).thenReturn(List.<Object[]>of(
                tese("id-1", "Tema 1", "autor", 6, 2, 10, 2, 20, atualizado)));

        IndicadorAdesao adesao = processoService.obterIndicadorAdesao("Dano Moral");

        assertThat(adesao.tese()).isEqualTo("Tema 1");
        assertThat(adesao.tribunalTese()).isEqualTo("STJ");
        assertThat(adesao.direcao()).isEqualTo("autor");
        assertThat(adesao.naoAderentes()).isEqualTo(2);
        assertThat(adesao.indice()).isEqualTo(70.0);
        assertThat(adesao.cobertura()).isEqualTo(50.0);
        assertThat(adesao.confiabilidade()).isEqualTo(Confiabilidade.BAIXA);
        assertThat(adesao.possuiTeseCurada()).isTrue();
        assertThat(adesao.atualizadoEm()).isEqualTo(OffsetDateTime.parse("2026-11-13T07:00:00-03:00"));
    }

    @Test
    void indicadorAdesaoSemTeseCuradaFicaSemIndice() {
        when(processoRepository.findAdesaoPorTese("Sem tese")).thenReturn(List.of());

        IndicadorAdesao adesao = processoService.obterIndicadorAdesao("Sem tese");

        assertThat(adesao.indice()).isNull();
        assertThat(adesao.cobertura()).isNull();
        assertThat(adesao.possuiTeseCurada()).isFalse();
        assertThat(adesao.confiabilidade()).isEqualTo(Confiabilidade.INSUFICIENTE);
    }

    @Test
    void tesePrincipalPrefereAmostraConfiavelETesesOpostasNaoSaoSomadas() {
        when(processoRepository.findAdesaoPorTese("Penhora")).thenReturn(List.<Object[]>of(
                tese("id-pequena", "Tese pequena", "autor", 2, 0, 2, 0, 5, null),
                tese("id-autor", "Tese do autor", "autor", 25, 2, 28, 1, 40, null),
                tese("id-reu", "Tese do réu", "reu", 1, 2, 28, 25, 40, null)));
        when(processoRepository.findTotaisPorPolo("Penhora")).thenReturn(List.of());
        when(processoRepository.findAdesaoPorOrgao("Penhora", "id-autor"))
                .thenReturn(List.<Object[]>of(new Object[]{"Vara A", 25L, 2L, 28L}));

        var indicadores = processoService.obterIndicadoresTema("Penhora");

        assertThat(indicadores.adesao().tese()).isEqualTo("Tese do autor");
        assertThat(indicadores.adesao().indice()).isEqualTo(92.86);
        assertThat(indicadores.adesaoPorOrgao()).extracting(AdesaoPorGrupo::nome).containsExactly("Vara A");
        assertThat(indicadores.adesaoPorTese()).extracting(AdesaoPorGrupo::indice)
                .containsExactly(100.0, 92.86, 7.14);
        verify(processoRepository).findAdesaoPorOrgao("Penhora", "id-autor");
    }

    @Test
    void temaSemTeseCuradaNaoConsultaOrgaos() {
        when(processoRepository.findAdesaoPorTese("Sem tese")).thenReturn(List.of());
        when(processoRepository.findTotaisPorPolo("Sem tese")).thenReturn(List.of());

        var indicadores = processoService.obterIndicadoresTema("Sem tese");

        assertThat(indicadores.adesao().possuiTeseCurada()).isFalse();
        assertThat(indicadores.adesaoPorOrgao()).isEmpty();
        assertThat(indicadores.polo().autorPct()).isNull();
    }

    @Test
    void adesaoPorOrgaoOrdenaPeloIndiceELimitaAQuinze() {
        List<Object[]> linhas = new ArrayList<>();
        linhas.add(new Object[]{"Vara baixa", 1L, 0L, 10L});
        linhas.add(new Object[]{"Vara alta", 9L, 0L, 10L});
        for (int i = 0; i < 20; i++) {
            linhas.add(new Object[]{"Vara " + i, 5L, 0L, 10L});
        }
        when(processoRepository.findAdesaoPorOrgao("Dano Moral", "id-1")).thenReturn(linhas);

        List<AdesaoPorGrupo> orgaos = processoService.obterAdesaoPorOrgao("Dano Moral", "id-1");

        assertThat(orgaos).hasSize(ProcessoService.LIMITE_ORGAOS);
        assertThat(orgaos.get(0).nome()).isEqualTo("Vara alta");
        assertThat(orgaos.get(0).indice()).isEqualTo(90.0);
        assertThat(orgaos).extracting(AdesaoPorGrupo::nome).doesNotContain("Vara baixa");
    }

    @Test
    void adesaoPorTeseUsaTituloQuandoNaoHaIdentificador() {
        when(processoRepository.findAdesaoPorTese("Dano Moral")).thenReturn(List.<Object[]>of(
                new Object[]{"id-1", null, "STJ", "Título da tese", "reu", 3L, 0L, 4L, 1L, 6L, null}));

        List<AdesaoPorGrupo> teses = processoService.obterAdesaoPorTese("Dano Moral");

        assertThat(teses).singleElement().satisfies(tese -> {
            assertThat(tese.nome()).isEqualTo("Título da tese");
            assertThat(tese.detalhe()).isEqualTo("STJ");
            assertThat(tese.direcao()).isEqualTo("reu");
            assertThat(tese.indice()).isEqualTo(75.0);
        });
    }

    @Test
    void evidenciasDaTesePrincipalConferemComOIndice() {
        Timestamp julgamento = Timestamp.from(Instant.parse("2026-06-01T15:00:00Z"));
        when(processoRepository.findAdesaoPorTese("Penhora")).thenReturn(List.<Object[]>of(
                tese("id-autor", "RR 677", "autor", 25, 2, 28, 1, 40, null)));
        when(processoRepository.findTotaisPorPolo("Penhora")).thenReturn(List.of());
        when(processoRepository.findEvidenciasPorTese("Penhora", "id-autor", ProcessoService.LIMITE_EVIDENCIAS))
                .thenReturn(List.<Object[]>of(
                        new Object[]{"00045844420218260562", "Vara A", "Procedência", julgamento, "aderente"},
                        new Object[]{"123", "Vara B", "Procedência em Parte", null, "parcial"}));
        when(processoRepository.findTotaisEvidenciasPorTese("Penhora", "id-autor"))
                .thenReturn(List.<Object[]>of(new Object[]{28L, 25L, 2L, 1L}));

        EvidenciasTese evidencias = processoService.obterIndicadoresTema("Penhora", null).evidencias();

        assertThat(evidencias.teseId()).isEqualTo("id-autor");
        assertThat(evidencias.tese()).isEqualTo("RR 677");
        assertThat(evidencias.direcao()).isEqualTo("autor");
        assertThat(evidencias.total()).isEqualTo(28);
        assertThat(evidencias.conferemComIndice()).isTrue();
        assertThat(evidencias.listaParcial()).isTrue();
        assertThat(evidencias.decisoes()).hasSize(2);
        EvidenciaDecisao primeira = evidencias.decisoes().get(0);
        assertThat(primeira.numeroProcesso()).isEqualTo("0004584-44.2021.8.26.0562");
        assertThat(primeira.dataJulgamento()).isEqualTo(LocalDate.of(2026, 6, 1));
        assertThat(primeira.classificacao()).isEqualTo(EvidenciaDecisao.Classificacao.ADERENTE);
        assertThat(evidencias.decisoes().get(1).numeroProcesso()).isEqualTo("123");
        assertThat(evidencias.decisoes().get(1).classificacao()).isEqualTo(EvidenciaDecisao.Classificacao.PARCIAL);
    }

    @Test
    void evidenciasUsamATeseSelecionadaQuandoPertenceAoTema() {
        when(processoRepository.findAdesaoPorTese("Penhora")).thenReturn(List.<Object[]>of(
                tese("id-autor", "RR 677", "autor", 25, 2, 28, 1, 40, null),
                tese("id-reu", "SUM 46", "reu", 1, 2, 28, 25, 40, null)));
        when(processoRepository.findTotaisPorPolo("Penhora")).thenReturn(List.of());
        when(processoRepository.findTotaisEvidenciasPorTese("Penhora", "id-reu"))
                .thenReturn(List.<Object[]>of(new Object[]{28L, 1L, 2L, 25L}));

        var indicadores = processoService.obterIndicadoresTema("Penhora", "id-reu");

        assertThat(indicadores.adesao().tese()).isEqualTo("RR 677");
        assertThat(indicadores.evidencias().tese()).isEqualTo("SUM 46");
        assertThat(indicadores.evidencias().conferemComIndice()).isTrue();
        verify(processoRepository).findEvidenciasPorTese("Penhora", "id-reu", ProcessoService.LIMITE_EVIDENCIAS);
    }

    @Test
    void teseDesconhecidaVoltaParaATesePrincipal() {
        when(processoRepository.findAdesaoPorTese("Penhora")).thenReturn(List.<Object[]>of(
                tese("id-autor", "RR 677", "autor", 25, 2, 28, 1, 40, null)));
        when(processoRepository.findTotaisPorPolo("Penhora")).thenReturn(List.of());

        var indicadores = processoService.obterIndicadoresTema("Penhora", "outro-tema");

        assertThat(indicadores.evidencias().teseId()).isEqualTo("id-autor");
    }

    @Test
    void evidenciasDivergentesDoIndiceSaoSinalizadas() {
        when(processoRepository.findAdesaoPorTese("Penhora")).thenReturn(List.<Object[]>of(
                tese("id-autor", "RR 677", "autor", 25, 2, 28, 1, 40, null)));
        when(processoRepository.findTotaisPorPolo("Penhora")).thenReturn(List.of());
        when(processoRepository.findTotaisEvidenciasPorTese("Penhora", "id-autor"))
                .thenReturn(List.<Object[]>of(new Object[]{27L, 24L, 2L, 1L}));

        assertThat(processoService.obterIndicadoresTema("Penhora", null).evidencias().conferemComIndice()).isFalse();
    }

    @Test
    void temaSemTeseCuradaNaoTemEvidencias() {
        when(processoRepository.findAdesaoPorTese("Sem tese")).thenReturn(List.of());
        when(processoRepository.findTotaisPorPolo("Sem tese")).thenReturn(List.of());

        assertThat(processoService.obterIndicadoresTema("Sem tese", null).evidencias()).isNull();
    }

    @Test
    void numeroCnjEhFormatado() {
        assertThat(ProcessoService.formatarNumeroProcesso("00045844420218260562")).isEqualTo("0004584-44.2021.8.26.0562");
        assertThat(ProcessoService.formatarNumeroProcesso("123")).isEqualTo("123");
        assertThat(ProcessoService.formatarNumeroProcesso(null)).isNull();
    }
}
