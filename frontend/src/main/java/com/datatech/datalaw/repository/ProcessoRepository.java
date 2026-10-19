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
            "  and (:assuntoNome IS NULL OR :assuntoNome = '' OR a.nome ILIKE concat('%', :assuntoNome, '%')) " +
            "group by p.classe_nome order by quantidade desc limit 50", nativeQuery = true)
    List<Object[]> findQuantidadeProcessosPorClasse(
            @Param("assuntoNome") String assuntoNome);

    @Query(value = "SELECT COALESCE(ROUND(100 * SUM(favoraveis + parciais * 0.5) / NULLIF(SUM(processos_com_resultado), 0), 2), 0) " +
            "FROM gold.process_results WHERE classe_nome = :classeNome", nativeQuery = true)
    Double findTaxaSucessoPorClasse(@Param("classeNome") String classeNome);

    @Query(value = "select a.nome, count(distinct p.id) as quantidade " +
            "from silver.processo p " +
            "join silver.processo_assunto a on a.processo_id = p.id " +
            "where a.nome is not null and a.nome != '' " +
            "  and (:classeNome IS NULL OR :classeNome = '' OR p.classe_nome ILIKE concat('%', :classeNome, '%')) " +
            "  and (:assuntoNome IS NULL OR :assuntoNome = '' OR a.nome ILIKE concat('%', :assuntoNome, '%')) " +
            "group by a.nome " +
            "having count(distinct p.id) >= 30 " +
            "order by quantidade desc limit 25", nativeQuery = true)
    List<Object[]> findQuantidadeProcessosPorAssunto(
            @Param("classeNome") String classeNome,
            @Param("assuntoNome") String assuntoNome);

    @Query(value = "SELECT COALESCE(ROUND(100 * SUM(favoraveis + parciais * 0.5) / NULLIF(SUM(processos_com_resultado), 0), 2), 0) " +
            "FROM gold.topic_results WHERE assunto_nome = :assuntoNome", nativeQuery = true)
    Double findTaxaSucessoPorAssunto(@Param("assuntoNome") String assuntoNome);
}
