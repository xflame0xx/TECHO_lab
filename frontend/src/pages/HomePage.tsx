import { Card, Col, Container, Row } from "react-bootstrap";
import { Link } from "react-router-dom";
import { AppBreadcrumbs } from "../components/AppBreadcrumbs";
import { ROUTES } from "../routes";

export const HomePage = () => {
  return (
    <Container className="page-container">
      <AppBreadcrumbs items={[]} />

      <Row className="align-items-center">
        <Col lg={7}>
          <h1 className="display-5 fw-bold">JobAbility</h1>

          <p className="lead">
            SPA-приложение для просмотра вакансий и услуг трудоустройства.
            Данные можно получать из mock-объектов или из Django REST API.
          </p>

          <Link to={ROUTES.VACANCIES} className="btn btn-primary btn-lg">
            Смотреть вакансии
          </Link>
        </Col>

        <Col lg={5} className="mt-4 mt-lg-0">
          <Card>
            <Card.Body>
              <Card.Title>Что реализовано</Card.Title>

              <ul className="mb-0">
                <li>React SPA на TypeScript.</li>
                <li>Три страницы приложения.</li>
                <li>Mock-режим без Django.</li>
                <li>Backend-режим через Vite proxy.</li>
                <li>Фильтры по названию, цене и дате.</li>
                <li>Изображение по умолчанию.</li>
              </ul>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};
