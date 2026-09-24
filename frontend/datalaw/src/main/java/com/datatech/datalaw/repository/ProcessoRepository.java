package com.datatech.datalaw.repository;

import com.datatech.datalaw.entity.dto.ProcessoDTOResponse;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.UUID;

public interface ProcessoRepository extends JpaRepository<ProcessoDTOResponse, UUID> {

    @Query("select orgao_julgador_nome, count(id) as quantidade " +
            "from silver.processo where classe_nome='Execução Fiscal' " +
            "group by orgao_julgador_nome order by orgao_julgador_nome;")
    List<Object[]> findQuantidadeProcessosPorOrgaoJulgador();
}
