package com.datatech.datalaw.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Column;

import java.util.UUID;

@Entity
@Table(name = "processo", schema = "silver")
public class Processo {

    @Id
    private UUID id;

    @Column(name = "orgao_julgador_nome")
    private String orgaoJulgadorNome;

    @Column(name = "classe_nome")
    private String classeNome;

    // Getters and Setters
    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public String getOrgaoJulgadorNome() {
        return orgaoJulgadorNome;
    }

    public void setOrgaoJulgadorNome(String orgaoJulgadorNome) {
        this.orgaoJulgadorNome = orgaoJulgadorNome;
    }

    public String getClasseNome() {
        return classeNome;
    }

    public void setClasseNome(String classeNome) {
        this.classeNome = classeNome;
    }
}
