package com.datatech.datalaw.service;

import com.datatech.datalaw.entity.dto.AdesaoPorGrupo;
import com.datatech.datalaw.entity.dto.Confiabilidade;
import com.datatech.datalaw.entity.dto.EvidenciaDecisao;
import com.datatech.datalaw.entity.dto.EvidenciasTese;
import com.datatech.datalaw.entity.dto.IndicadorAdesao;
import com.datatech.datalaw.entity.dto.IndicadoresTema;
import com.datatech.datalaw.entity.dto.ResultadoPorPolo;
import com.datatech.datalaw.repository.ProcessoRepository;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.util.Comparator;
import java.util.List;

@Service
public class ProcessoService {

    static final int LIMITE_ORGAOS = 15;

    static final int LIMITE_EVIDENCIAS = 50;

    static final ZoneId FUSO_EXIBICAO = ZoneId.of("America/Sao_Paulo");

    private static final Comparator<AdesaoPorGrupo> PELO_INDICE = Comparator
            .comparing(AdesaoPorGrupo::indice, Comparator.nullsLast(Comparator.reverseOrder()))
            .thenComparing(AdesaoPorGrupo::decisoesComResultado, Comparator.reverseOrder());

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

    public IndicadoresTema obterIndicadoresTema(String assuntoNome) {
        return obterIndicadoresTema(assuntoNome, null);
    }

    /**
     * Indicators of a topic. The evidence section shows the thesis {@code teseId}
     * when it belongs to the topic, otherwise the main thesis.
     */
    public IndicadoresTema obterIndicadoresTema(String assuntoNome, String teseId) {
        List<Object[]> linhasTeses = processoRepository.findAdesaoPorTese(assuntoNome);
        Object[] principal = tesePrincipal(linhasTeses);
        Object[] selecionada = linhasTeses.stream()
                .filter(linha -> teseId != null && teseId.equals(linha[0]))
                .findFirst()
                .orElse(principal);
        return new IndicadoresTema(
                indicadorAdesao(principal),
                obterResultadoPorPolo(assuntoNome),
                principal == null ? List.of() : obterAdesaoPorOrgao(assuntoNome, (String) principal[0]),
                adesaoPorTese(linhasTeses),
                selecionada == null ? null : evidencias(assuntoNome, selecionada));
    }

    public IndicadorAdesao obterIndicadorAdesao(String assuntoNome) {
        return indicadorAdesao(tesePrincipal(processoRepository.findAdesaoPorTese(assuntoNome)));
    }

    public ResultadoPorPolo obterResultadoPorPolo(String assuntoNome) {
        Object[] linha = primeiraLinha(processoRepository.findTotaisPorPolo(assuntoNome), 6);
        long procedentes = inteiro(linha[0]);
        long parciais = inteiro(linha[1]);
        long improcedentes = inteiro(linha[2]);
        long decisoes = inteiro(linha[3]);
        return new ResultadoPorPolo(
                percentual(procedentes, parciais, decisoes),
                percentual(improcedentes, parciais, decisoes),
                procedentes,
                parciais,
                improcedentes,
                decisoes,
                inteiro(linha[4]),
                Confiabilidade.paraAmostra(decisoes),
                dataHora(linha[5]));
    }

    /**
     * Compares judging bodies for one thesis only, since theses with opposite
     * directions would cancel each other out.
     */
    public List<AdesaoPorGrupo> obterAdesaoPorOrgao(String assuntoNome, String teseId) {
        return processoRepository.findAdesaoPorOrgao(assuntoNome, teseId).stream()
                .map(linha -> grupo(null, (String) linha[0], null, null, linha[1], linha[2], linha[3]))
                .sorted(PELO_INDICE)
                .limit(LIMITE_ORGAOS)
                .toList();
    }

    public List<AdesaoPorGrupo> obterAdesaoPorTese(String assuntoNome) {
        return adesaoPorTese(processoRepository.findAdesaoPorTese(assuntoNome));
    }

    private static List<AdesaoPorGrupo> adesaoPorTese(List<Object[]> linhas) {
        return linhas.stream()
                .map(linha -> grupo((String) linha[0], nomeTese(linha), (String) linha[2], (String) linha[4],
                        linha[5], linha[6], linha[7]))
                .sorted(PELO_INDICE)
                .toList();
    }

    /**
     * The main thesis: the most reliable and largest sample first, then the highest index,
     * so a thesis with a handful of decisions never outranks a well-supported one.
     */
    private static Object[] tesePrincipal(List<Object[]> linhas) {
        return linhas.stream()
                .min(Comparator
                        .comparing((Object[] linha) -> Confiabilidade.paraAmostra(inteiro(linha[7])),
                                Comparator.reverseOrder())
                        .thenComparing(linha -> inteiro(linha[7]), Comparator.reverseOrder())
                        .thenComparing(linha -> percentual(inteiro(linha[5]), inteiro(linha[6]), inteiro(linha[7])),
                                Comparator.nullsLast(Comparator.reverseOrder())))
                .orElse(null);
    }

    private static IndicadorAdesao indicadorAdesao(Object[] linha) {
        if (linha == null) {
            return IndicadorAdesao.semTeseCurada();
        }
        long aderentes = inteiro(linha[5]);
        long parciais = inteiro(linha[6]);
        long decisoes = inteiro(linha[7]);
        long encerrados = inteiro(linha[9]);
        return new IndicadorAdesao(
                nomeTese(linha),
                (String) linha[2],
                (String) linha[4],
                percentual(aderentes, parciais, decisoes),
                aderentes,
                parciais,
                inteiro(linha[8]),
                decisoes,
                encerrados,
                cobertura(decisoes, encerrados),
                Confiabilidade.paraAmostra(decisoes),
                dataHora(linha[10]));
    }

    /**
     * Decisions behind one thesis. The totals are checked against the counts of the
     * index, so the evidence always explains the number shown on the dashboard.
     */
    private EvidenciasTese evidencias(String assuntoNome, Object[] tese) {
        String teseId = (String) tese[0];
        List<EvidenciaDecisao> decisoes = processoRepository
                .findEvidenciasPorTese(assuntoNome, teseId, LIMITE_EVIDENCIAS).stream()
                .map(linha -> new EvidenciaDecisao(
                        formatarNumeroProcesso((String) linha[0]),
                        (String) linha[1],
                        (String) linha[2],
                        data(linha[3]),
                        EvidenciaDecisao.Classificacao.deGold((String) linha[4])))
                .toList();
        Object[] totais = primeiraLinha(processoRepository.findTotaisEvidenciasPorTese(assuntoNome, teseId), 4);
        long total = inteiro(totais[0]);
        long aderentes = inteiro(totais[1]);
        long parciais = inteiro(totais[2]);
        long naoAderentes = inteiro(totais[3]);
        boolean conferem = total == inteiro(tese[7])
                && aderentes == inteiro(tese[5])
                && parciais == inteiro(tese[6])
                && naoAderentes == inteiro(tese[8]);
        return new EvidenciasTese(teseId, nomeTese(tese), (String) tese[2], (String) tese[4],
                decisoes, total, aderentes, parciais, naoAderentes, conferem, LIMITE_EVIDENCIAS);
    }

    /**
     * Formats a 20-digit CNJ number as NNNNNNN-DD.AAAA.J.TR.OOOO; other values are kept.
     */
    static String formatarNumeroProcesso(String numero) {
        if (numero == null || !numero.matches("\\d{20}")) {
            return numero;
        }
        return numero.substring(0, 7) + "-" + numero.substring(7, 9) + "." + numero.substring(9, 13) + "."
                + numero.substring(13, 14) + "." + numero.substring(14, 16) + "." + numero.substring(16);
    }

    private static String nomeTese(Object[] linha) {
        return linha[1] != null ? (String) linha[1] : (String) linha[3];
    }

    /**
     * 100 × (favorable + 0.5 × partial) / decisions, rounded to two decimals.
     * Returns null when there are no decisions, so missing data is never shown as 0%.
     */
    static Double percentual(long favoraveis, long parciais, long decisoes) {
        if (decisoes <= 0) {
            return null;
        }
        return BigDecimal.valueOf(favoraveis)
                .add(BigDecimal.valueOf(parciais).multiply(new BigDecimal("0.5")))
                .multiply(BigDecimal.valueOf(100))
                .divide(BigDecimal.valueOf(decisoes), 2, RoundingMode.HALF_UP)
                .doubleValue();
    }

    static Double cobertura(long decisoes, long encerrados) {
        if (encerrados <= 0) {
            return null;
        }
        return BigDecimal.valueOf(decisoes)
                .multiply(BigDecimal.valueOf(100))
                .divide(BigDecimal.valueOf(encerrados), 2, RoundingMode.HALF_UP)
                .doubleValue();
    }

    private static AdesaoPorGrupo grupo(String id, String nome, String detalhe, String direcao,
                                        Object aderentes, Object parciais, Object decisoes) {
        long total = inteiro(decisoes);
        return new AdesaoPorGrupo(
                id,
                nome,
                detalhe,
                direcao,
                percentual(inteiro(aderentes), inteiro(parciais), total),
                total,
                Confiabilidade.paraAmostra(total));
    }

    private static Object[] primeiraLinha(List<Object[]> linhas, int colunas) {
        if (linhas == null || linhas.isEmpty() || linhas.get(0) == null) {
            return new Object[colunas];
        }
        return linhas.get(0);
    }

    private static long inteiro(Object valor) {
        return valor instanceof Number numero ? numero.longValue() : 0L;
    }

    private static LocalDate data(Object valor) {
        OffsetDateTime dataHora = dataHora(valor);
        return dataHora == null ? null : dataHora.toLocalDate();
    }

    private static OffsetDateTime dataHora(Object valor) {
        Instant instante = null;
        if (valor instanceof OffsetDateTime dataHora) {
            instante = dataHora.toInstant();
        } else if (valor instanceof Instant valorInstante) {
            instante = valorInstante;
        } else if (valor instanceof Timestamp timestamp) {
            instante = timestamp.toInstant();
        }
        return instante == null ? null : instante.atZone(FUSO_EXIBICAO).toOffsetDateTime();
    }
}
