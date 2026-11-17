package com.datatech.datalaw.repository;

import com.datatech.datalaw.entity.Processo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.UUID;

public interface ProcessoRepository extends JpaRepository<Processo, UUID> {

    @Query(value = "select p.orgao_julgador_nome, count(distinct p.id) as quantidade " +
            "from silver.processo p " +
            "left join silver.processo_assunto a on a.processo_id = p.id " +
            "where p.orgao_julgador_nome is not null and p.orgao_julgador_nome != '' " +
            "  and coalesce(p.nivel_sigilo, 0) = 0 " +
            "  and (:classeNome IS NULL OR :classeNome = '' OR p.classe_nome ILIKE concat('%', :classeNome, '%')) " +
            "  and (:assuntoNome IS NULL OR :assuntoNome = '' OR a.nome ILIKE concat('%', :assuntoNome, '%')) " +
            "group by p.orgao_julgador_nome order by quantidade desc limit 50", nativeQuery = true)
    List<Object[]> findQuantidadeProcessosPorOrgaoJulgador(
            @Param("classeNome") String classeNome,
            @Param("assuntoNome") String assuntoNome);

    @Query(value = "select p.classe_nome, count(distinct p.id) as quantidade " +
            "from silver.processo p " +
            "left join silver.processo_assunto a on a.processo_id = p.id " +
            "where p.classe_nome is not null and p.classe_nome != '' " +
            "  and coalesce(p.nivel_sigilo, 0) = 0 " +
            "  and (:assuntoNome IS NULL OR :assuntoNome = '' OR a.nome ILIKE concat('%', :assuntoNome, '%')) " +
            "group by p.classe_nome order by quantidade desc limit 50", nativeQuery = true)
    List<Object[]> findQuantidadeProcessosPorClasse(
            @Param("assuntoNome") String assuntoNome);

    @Query(value = "SELECT ROUND(100 * SUM(favoraveis + parciais * 0.5) / NULLIF(SUM(processos_com_resultado), 0), 2) " +
            "FROM gold.process_results WHERE classe_nome = :classeNome", nativeQuery = true)
    Double findTaxaSucessoPorClasse(@Param("classeNome") String classeNome);

    @Query(value = "select a.nome, count(distinct p.id) as quantidade " +
            "from silver.processo p " +
            "join silver.processo_assunto a on a.processo_id = p.id " +
            "where a.nome is not null and a.nome != '' " +
            "  and coalesce(p.nivel_sigilo, 0) = 0 " +
            "  and (:classeNome IS NULL OR :classeNome = '' OR p.classe_nome ILIKE concat('%', :classeNome, '%')) " +
            "  and (:assuntoNome IS NULL OR :assuntoNome = '' OR a.nome ILIKE concat('%', :assuntoNome, '%')) " +
            "group by a.nome " +
            "having count(distinct p.id) >= 30 " +
            "order by quantidade desc limit 25", nativeQuery = true)
    List<Object[]> findQuantidadeProcessosPorAssunto(
            @Param("classeNome") String classeNome,
            @Param("assuntoNome") String assuntoNome);

    @Query(value = "SELECT ROUND(100 * SUM(favoraveis + parciais * 0.5) / NULLIF(SUM(processos_com_resultado), 0), 2) " +
            "FROM gold.topic_results WHERE assunto_nome = :assuntoNome", nativeQuery = true)
    Double findTaxaSucessoPorAssunto(@Param("assuntoNome") String assuntoNome);

    @Query(value = "SELECT tribunal_precedente, identificador_precedente, precedente_titulo, precedente_tese, precedente_ementa " +
            "FROM gold.topic_precedents WHERE assunto_nome = :assuntoNome ORDER BY identificador_precedente", nativeQuery = true)
    List<Object[]> findPrecedentesPorAssunto(@Param("assuntoNome") String assuntoNome);

    @Query(value = "SELECT orgao_julgador_nome, SUM(aderentes), SUM(parciais), SUM(decisoes_com_resultado) " +
            "FROM gold.topic_adherence " +
            "WHERE assunto_nome ILIKE concat('%', :assuntoNome, '%') AND CAST(jurisprudencia_id AS text) = :teseId " +
            "AND orgao_julgador_nome IS NOT NULL " +
            "GROUP BY orgao_julgador_nome HAVING SUM(decisoes_com_resultado) > 0", nativeQuery = true)
    List<Object[]> findAdesaoPorOrgao(@Param("assuntoNome") String assuntoNome, @Param("teseId") String teseId);

    @Query(value = "SELECT CAST(jurisprudencia_id AS text), identificador_precedente, tribunal_precedente, " +
            "precedente_titulo, direcao, " +
            "SUM(aderentes), SUM(parciais), SUM(decisoes_com_resultado), SUM(nao_aderentes), " +
            "SUM(processos_encerrados), MAX(atualizado_em) " +
            "FROM gold.topic_adherence WHERE assunto_nome ILIKE concat('%', :assuntoNome, '%') " +
            "GROUP BY jurisprudencia_id, identificador_precedente, tribunal_precedente, precedente_titulo, direcao", nativeQuery = true)
    List<Object[]> findAdesaoPorTese(@Param("assuntoNome") String assuntoNome);

    @Query(value = "SELECT COALESCE(SUM(procedentes), 0), COALESCE(SUM(parciais), 0), COALESCE(SUM(improcedentes), 0), " +
            "COALESCE(SUM(decisoes_com_resultado), 0), COALESCE(SUM(processos_encerrados), 0), MAX(atualizado_em) " +
            "FROM gold.topic_party_results WHERE assunto_nome ILIKE concat('%', :assuntoNome, '%')", nativeQuery = true)
    List<Object[]> findTotaisPorPolo(@Param("assuntoNome") String assuntoNome);

    @Query(value = "SELECT numero_processo, orgao_julgador_nome, movimento_nome, data_julgamento, classificacao " +
            "FROM gold.topic_adherence_evidence " +
            "WHERE assunto_nome ILIKE concat('%', :assuntoNome, '%') AND CAST(jurisprudencia_id AS text) = :teseId " +
            "ORDER BY data_julgamento DESC, numero_processo LIMIT :limite", nativeQuery = true)
    List<Object[]> findEvidenciasPorTese(@Param("assuntoNome") String assuntoNome,
                                         @Param("teseId") String teseId,
                                         @Param("limite") int limite);

    @Query(value = "SELECT COUNT(*), COUNT(*) FILTER (WHERE classificacao = 'aderente'), " +
            "COUNT(*) FILTER (WHERE classificacao = 'parcial'), COUNT(*) FILTER (WHERE classificacao = 'nao_aderente') " +
            "FROM gold.topic_adherence_evidence " +
            "WHERE assunto_nome ILIKE concat('%', :assuntoNome, '%') AND CAST(jurisprudencia_id AS text) = :teseId",
            nativeQuery = true)
    List<Object[]> findTotaisEvidenciasPorTese(@Param("assuntoNome") String assuntoNome,
                                               @Param("teseId") String teseId);
}
